from decimal import Decimal, ROUND_HALF_UP
from os import error

import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("banking.database")

from src.api.database import get_db_connection
from rules.risk_rules import calculate_customer_risk


EXPECTED_MONTHS = {
    "2005-04-01",
    "2005-05-01",
    "2005-06-01",
    "2005-07-01",
    "2005-08-01",
    "2005-09-01"
}


def validate_activity_months(monthly_activity):

    received_months = {
        activity.activity_month.isoformat()
        for activity in monthly_activity
    }

    if received_months != EXPECTED_MONTHS:
        raise ValueError(
            "monthly_activity must contain exactly one "
            "record for each month from "
            "2005-04-01 through 2005-09-01"
        )


def build_credit_profile(request):

    activity = sorted(
        request.monthly_activity,
        key=lambda item: item.activity_month
    )

    repayment_statuses = [
        item.repayment_status
        for item in activity
    ]

    bill_amounts = [
        item.bill_amount
        for item in activity
    ]

    payment_amounts = [
        item.payment_amount
        for item in activity
    ]

    delay_month_count = sum(
        status > 0
        for status in repayment_statuses
    )

    max_delay_status = max(
        max(repayment_statuses),
        0
    )

    has_payment_delay = (
        delay_month_count > 0
    )

    total_bill_amount_6m = sum(
        bill_amounts
    )

    average_bill_amount_6m = (
        total_bill_amount_6m / 6
    )

    total_payment_amount_6m = sum(
        payment_amounts
    )

    average_payment_amount_6m = (
        total_payment_amount_6m / 6
    )

    # September is the latest month.
    latest_bill_amount = next(
        item.bill_amount
        for item in activity
        if item.activity_month.isoformat()
        == "2005-09-01"
    )

    utilization = (
        Decimal(str(latest_bill_amount))
        / Decimal(str(request.credit_limit))
    ).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP
    )

    return {
        "delay_month_count":
            delay_month_count,

        "max_delay_status":
            max_delay_status,

        "has_payment_delay":
            has_payment_delay,

        "total_bill_amount_6m":
            total_bill_amount_6m,

        "average_bill_amount_6m":
            round(average_bill_amount_6m, 2),

        "total_payment_amount_6m":
            total_payment_amount_6m,

        "average_payment_amount_6m":
            round(average_payment_amount_6m, 2),

        "latest_utilization_ratio":
            float(utilization)
    }



def calculate_risk_for_request(
    request,
    profile
):

    risk_input = pd.Series({
        "delay_month_count":
            profile["delay_month_count"],

        "max_delay_status":
            profile["max_delay_status"],

        "latest_utilization_ratio":
            profile[
                "latest_utilization_ratio"
            ],

        "total_bill_amount_6m":
            profile[
                "total_bill_amount_6m"
            ],

        "total_payment_amount_6m":
            profile[
                "total_payment_amount_6m"
            ]
    })

    return calculate_customer_risk(
        risk_input
    )



def create_customer(request):

    validate_activity_months(
        request.monthly_activity
    )

    profile = build_credit_profile(
        request
    )

    risk = calculate_risk_for_request(
        request,
        profile
    )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # ---------------------------------------
        # Duplicate check
        # ---------------------------------------

        cursor.execute(
        """
        SELECT customer_id
        FROM customers
        WHERE customer_id = %s
        """,
        (request.customer_id,)
)

        if cursor.fetchone() is not None:
            connection.rollback()

            return {
                "status": "duplicate"
            }

        # ---------------------------------------
        # Start transaction
        # ---------------------------------------

        # connection.start_transaction()

        # ---------------------------------------
        # customers
        # ---------------------------------------

        cursor.execute(
    """
    INSERT INTO customers (
        customer_id,
        gender_code,
        education_code,
        marital_status_code,
        age
    )
    VALUES (%s, %s, %s, %s, %s)
    """,
    (
        request.customer_id,
        request.gender_code,
        request.education_code,
        request.marital_status_code,
        request.age
    )
)

        # ---------------------------------------
        # credit_profiles
        # ---------------------------------------

        cursor.execute(
            """
            INSERT INTO credit_profiles (
                customer_id,
                credit_limit,
                delay_month_count,
                max_delay_status,
                has_payment_delay,
                total_bill_amount_6m,
                average_bill_amount_6m,
                total_payment_amount_6m,
                average_payment_amount_6m,
                latest_utilization_ratio,
                default_next_month
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            """,
            (
                request.customer_id,
                request.credit_limit,
                profile["delay_month_count"],
                profile["max_delay_status"],
                profile["has_payment_delay"],
                profile["total_bill_amount_6m"],
                profile["average_bill_amount_6m"],
                profile["total_payment_amount_6m"],
                profile["average_payment_amount_6m"],
                profile["latest_utilization_ratio"],
                request.default_next_month
            )
        )

        # ---------------------------------------
        # monthly_credit_activity
        # ---------------------------------------

        activity_values = [
            (
                request.customer_id,
                item.activity_month,
                item.repayment_status,
                item.bill_amount,
                item.payment_amount
            )
            for item in request.monthly_activity
        ]

        cursor.executemany(
            """
            INSERT INTO monthly_credit_activity (
                customer_id,
                activity_month,
                repayment_status,
                bill_amount,
                payment_amount
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            activity_values
        )

        # ---------------------------------------
        # customer_risk_assessment
        # ---------------------------------------

        cursor.execute(
            """
            INSERT INTO customer_risk_assessment (
                customer_id,
                payment_to_bill_ratio,
                delay_frequency_score,
                delay_severity_score,
                utilization_score,
                payment_behavior_score,
                risk_score,
                risk_band,
                rule_version
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                request.customer_id,
                risk["payment_to_bill_ratio"],
                risk["delay_frequency_score"],
                risk["delay_severity_score"],
                risk["utilization_score"],
                risk["payment_behavior_score"],
                risk["risk_score"],
                risk["risk_band"],
                "1.0"
            )
        )

        connection.commit()

        return {
            "status": "created",
            "customer_id":
                request.customer_id,
            "risk_score":
                risk["risk_score"],
            "risk_band":
                risk["risk_band"]
        }

    except Exception:
        logger.error(
        "Customer create transaction failed | error_type=%s",
        type(error).__name__,
    )
        if connection:
            connection.rollback()

        raise

    finally:
        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()


def update_customer(
    customer_id,
    request
):

    # Validate that exactly the expected
    # six months were supplied.
    validate_activity_months(
        request.monthly_activity
    )

    # Recalculate all derived profile fields.
    profile = build_credit_profile(
        request
    )

    # Recalculate risk using our existing
    # rule engine.
    risk = calculate_risk_for_request(
        request,
        profile
    )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # ---------------------------------------
        # Check customer exists
        # ---------------------------------------

        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        if cursor.fetchone() is None:
            connection.rollback()

            return {
                "status": "not_found"
            }

        # ---------------------------------------
        # Update customers
        # ---------------------------------------

        cursor.execute(
            """
            UPDATE customers
            SET
                gender_code = %s,
                education_code = %s,
                marital_status_code = %s,
                age = %s
            WHERE customer_id = %s
            """,
            (
                request.gender_code,
                request.education_code,
                request.marital_status_code,
                request.age,
                customer_id
            )
        )

        # ---------------------------------------
        # Update credit profile
        # ---------------------------------------

        cursor.execute(
            """
            UPDATE credit_profiles
            SET
                credit_limit = %s,
                delay_month_count = %s,
                max_delay_status = %s,
                has_payment_delay = %s,
                total_bill_amount_6m = %s,
                average_bill_amount_6m = %s,
                total_payment_amount_6m = %s,
                average_payment_amount_6m = %s,
                latest_utilization_ratio = %s,
                default_next_month = %s
            WHERE customer_id = %s
            """,
            (
                request.credit_limit,

                profile[
                    "delay_month_count"
                ],

                profile[
                    "max_delay_status"
                ],

                profile[
                    "has_payment_delay"
                ],

                profile[
                    "total_bill_amount_6m"
                ],

                profile[
                    "average_bill_amount_6m"
                ],

                profile[
                    "total_payment_amount_6m"
                ],

                profile[
                    "average_payment_amount_6m"
                ],

                profile[
                    "latest_utilization_ratio"
                ],

                request.default_next_month,

                customer_id
            )
        )

        # ---------------------------------------
        # Update six monthly records
        # ---------------------------------------

        activity_values = [
            (
                item.repayment_status,
                item.bill_amount,
                item.payment_amount,
                customer_id,
                item.activity_month
            )
            for item in request.monthly_activity
        ]

        cursor.executemany(
            """
            UPDATE monthly_credit_activity
            SET
                repayment_status = %s,
                bill_amount = %s,
                payment_amount = %s
            WHERE
                customer_id = %s
                AND activity_month = %s
            """,
            activity_values
        )

        # ---------------------------------------
        # Update risk assessment
        # ---------------------------------------

        cursor.execute(
            """
            UPDATE customer_risk_assessment
            SET
                payment_to_bill_ratio = %s,
                delay_frequency_score = %s,
                delay_severity_score = %s,
                utilization_score = %s,
                payment_behavior_score = %s,
                risk_score = %s,
                risk_band = %s,
                rule_version = %s
            WHERE customer_id = %s
            """,
            (
                risk[
                    "payment_to_bill_ratio"
                ],

                risk[
                    "delay_frequency_score"
                ],

                risk[
                    "delay_severity_score"
                ],

                risk[
                    "utilization_score"
                ],

                risk[
                    "payment_behavior_score"
                ],

                risk[
                    "risk_score"
                ],

                risk[
                    "risk_band"
                ],

                "1.0",

                customer_id
            )
        )

        connection.commit()

        return {
            "status": "updated",
            "customer_id": customer_id,
            "risk_score":
                risk["risk_score"],
            "risk_band":
                risk["risk_band"]
        }

    except Exception:

   
        logger.error(
        "Customer update transaction failed | error_type=%s",
            type(error).__name__,
    )

        if connection:
            connection.rollback()

        raise

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()



def delete_customer(customer_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check whether customer exists
        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        if cursor.fetchone() is None:
            connection.rollback()

            return {
                "status": "not_found"
            }

        # 1. Delete risk assessment
        cursor.execute(
            """
            DELETE FROM customer_risk_assessment
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        # 2. Delete monthly activity
        cursor.execute(
            """
            DELETE FROM monthly_credit_activity
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        # 3. Delete credit profile
        cursor.execute(
            """
            DELETE FROM credit_profiles
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        # 4. Delete customer
        cursor.execute(
            """
            DELETE FROM customers
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        connection.commit()

        return {
            "status": "deleted",
            "customer_id": customer_id
        }

    except Exception:

        logger.error(
        "Customer delete transaction failed | error_type=%s",
        type(error).__name__,
    )

        if connection:
            connection.rollback()

        raise

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()