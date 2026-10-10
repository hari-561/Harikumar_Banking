import math

from src.api.database import get_db_connection


def get_customers(
    page: int,
    page_size: int,
    risk_band: str | None = None,
    has_payment_delay: bool | None = None,
    min_credit_limit: float | None = None,
    max_credit_limit: float | None = None,
    sort_by: str = "customer_id",
    sort_order: str = "asc"
):
    """
    Retrieve customers with pagination and optional filters.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        where_conditions = []
        parameters = []

        # ----------------------------------------------------
        # Filters
        # ----------------------------------------------------

        if risk_band is not None:
            where_conditions.append(
                "r.risk_band = %s"
            )
            parameters.append(risk_band)

        if has_payment_delay is not None:
            where_conditions.append(
                "cp.has_payment_delay = %s"
            )
            parameters.append(
                1 if has_payment_delay else 0
            )

        if min_credit_limit is not None:
            where_conditions.append(
                "cp.credit_limit >= %s"
            )
            parameters.append(min_credit_limit)

        if max_credit_limit is not None:
            where_conditions.append(
                "cp.credit_limit <= %s"
            )
            parameters.append(max_credit_limit)

        where_clause = ""

        if where_conditions:
            where_clause = (
                " WHERE "
                + " AND ".join(where_conditions)
            )

        # ----------------------------------------------------
        # Count query
        # ----------------------------------------------------

        count_query = f"""
            SELECT COUNT(*) AS total_records

            FROM customers c

            INNER JOIN credit_profiles cp
                ON c.customer_id = cp.customer_id

            INNER JOIN dim_gender g
                ON c.gender_code = g.gender_code

            INNER JOIN dim_education e
                ON c.education_code = e.education_code

            INNER JOIN dim_marital_status m
                ON c.marital_status_code =
                   m.marital_status_code

            INNER JOIN customer_risk_assessment r
                ON c.customer_id = r.customer_id

            {where_clause}
        """

        cursor.execute(
            count_query,
            tuple(parameters)
        )

        total_records = (
            cursor.fetchone()["total_records"]
        )

        # ----------------------------------------------------
        # Pagination
        # ----------------------------------------------------

        total_pages = (
            math.ceil(total_records / page_size)
            if total_records > 0
            else 0
        )

        offset = (
            page - 1
        ) * page_size





        sort_columns = {
    "customer_id": "c.customer_id",
    "credit_limit": "cp.credit_limit",
    "latest_utilization_ratio":
        "cp.latest_utilization_ratio",
    "delay_month_count":
        "cp.delay_month_count",
    "risk_score": "r.risk_score"
}

        sort_column = sort_columns[sort_by]

        sql_sort_order = (
            "DESC"
            if sort_order == "desc"
            else "ASC"
)

        # ----------------------------------------------------
        # Data query
        # ----------------------------------------------------

        data_query = f"""
    SELECT
        c.customer_id,
        c.age,
        g.gender_name AS gender,
        e.education_name AS education,
        m.marital_status_name AS marital_status,
        cp.credit_limit,
        cp.has_payment_delay,
        cp.delay_month_count,
        cp.latest_utilization_ratio,
        r.risk_score,
        r.risk_band

    FROM customers c

    INNER JOIN credit_profiles cp
        ON c.customer_id = cp.customer_id

    INNER JOIN dim_gender g
        ON c.gender_code = g.gender_code

    INNER JOIN dim_education e
        ON c.education_code = e.education_code

    INNER JOIN dim_marital_status m
        ON c.marital_status_code =
           m.marital_status_code

    INNER JOIN customer_risk_assessment r
        ON c.customer_id = r.customer_id

    {where_clause}

    ORDER BY {sort_column} {sql_sort_order},
             c.customer_id ASC

    LIMIT %s OFFSET %s
"""

        data_parameters = (
            parameters
            + [
                page_size,
                offset
            ]
        )

        cursor.execute(
            data_query,
            tuple(data_parameters)
        )

        rows = cursor.fetchall()

        # ----------------------------------------------------
        # MySQL -> API-friendly values
        # ----------------------------------------------------

        for row in rows:

            row["credit_limit"] = float(
                row["credit_limit"]
            )

            row["latest_utilization_ratio"] = float(
                row["latest_utilization_ratio"]
            )

            row["has_payment_delay"] = bool(
                row["has_payment_delay"]
            )

        return {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages,
            "items": rows
        }

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()


def get_customer_by_id(customer_id: int):
    """
    Retrieve the complete profile and risk assessment
    for one customer.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                c.customer_id,
                c.age,

                g.gender_name AS gender,
                e.education_name AS education,
                m.marital_status_name
                    AS marital_status,

                cp.credit_limit,
                cp.delay_month_count,
                cp.max_delay_status,
                cp.has_payment_delay,

                cp.total_bill_amount_6m,
                cp.average_bill_amount_6m,

                cp.total_payment_amount_6m,
                cp.average_payment_amount_6m,

                cp.latest_utilization_ratio,
                cp.default_next_month,

                r.payment_to_bill_ratio,

                r.delay_frequency_score,
                r.delay_severity_score,
                r.utilization_score,
                r.payment_behavior_score,

                r.risk_score,
                r.risk_band,
                r.rule_version

            FROM customers c

            INNER JOIN dim_gender g
                ON c.gender_code = g.gender_code

            INNER JOIN dim_education e
                ON c.education_code = e.education_code

            INNER JOIN dim_marital_status m
                ON c.marital_status_code =
                   m.marital_status_code

            INNER JOIN credit_profiles cp
                ON c.customer_id = cp.customer_id

            INNER JOIN customer_risk_assessment r
                ON c.customer_id = r.customer_id

            WHERE c.customer_id = %s
        """

        cursor.execute(
            query,
            (customer_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "customer_id": row["customer_id"],

            "demographics": {
                "gender": row["gender"],
                "education": row["education"],
                "marital_status": row[
                    "marital_status"
                ],
                "age": row["age"]
            },

            "credit_profile": {
                "credit_limit": float(
                    row["credit_limit"]
                ),

                "delay_month_count":
                    row["delay_month_count"],

                "max_delay_status":
                    row["max_delay_status"],

                "has_payment_delay": bool(
                    row["has_payment_delay"]
                ),

                "total_bill_amount_6m": float(
                    row["total_bill_amount_6m"]
                ),

                "average_bill_amount_6m": float(
                    row["average_bill_amount_6m"]
                ),

                "total_payment_amount_6m": float(
                    row["total_payment_amount_6m"]
                ),

                "average_payment_amount_6m": float(
                    row["average_payment_amount_6m"]
                ),

                "latest_utilization_ratio": float(
                    row["latest_utilization_ratio"]
                ),

                "default_next_month":
                    row["default_next_month"]
            },

            "risk": {
                "payment_to_bill_ratio": (
                    float(
                        row[
                            "payment_to_bill_ratio"
                        ]
                    )
                    if row[
                        "payment_to_bill_ratio"
                    ] is not None
                    else None
                ),

                "delay_frequency_score":
                    row["delay_frequency_score"],

                "delay_severity_score":
                    row["delay_severity_score"],

                "utilization_score":
                    row["utilization_score"],

                "payment_behavior_score":
                    row["payment_behavior_score"],

                "risk_score":
                    row["risk_score"],

                "risk_band":
                    row["risk_band"],

                "rule_version":
                    row["rule_version"]
            }
        }

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()



def get_customer_activity(customer_id: int):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # First verify that the customer exists.
        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        if cursor.fetchone() is None:
            return None

        cursor.execute(
            """
            SELECT
                activity_month,
                repayment_status,
                bill_amount,
                payment_amount
            FROM monthly_credit_activity
            WHERE customer_id = %s
            ORDER BY activity_month
            """,
            (customer_id,)
        )

        rows = cursor.fetchall()

        for row in rows:
            row["bill_amount"] = float(
                row["bill_amount"]
            )

            row["payment_amount"] = float(
                row["payment_amount"]
            )

        return {
            "customer_id": customer_id,
            "activity": rows
        }

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_customer_risk(customer_id: int):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                r.customer_id,
                r.payment_to_bill_ratio,
                r.delay_frequency_score,
                r.delay_severity_score,
                r.utilization_score,
                r.payment_behavior_score,
                r.risk_score,
                r.risk_band,
                r.rule_version

            FROM customer_risk_assessment r

            WHERE r.customer_id = %s
            """,
            (customer_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        if row["payment_to_bill_ratio"] is not None:
            row["payment_to_bill_ratio"] = float(
                row["payment_to_bill_ratio"]
            )

        return row

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()