from src.api.database import get_db_connection


def get_portfolio_summary():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                COUNT(*) AS total_customers,

                SUM(credit_limit)
                    AS total_credit_exposure,

                AVG(credit_limit)
                    AS average_credit_limit,

                SUM(default_next_month)
                    AS historical_defaults,

                AVG(default_next_month) * 100
                    AS historical_default_rate_pct,

                SUM(has_payment_delay)
                    AS customers_with_payment_delay,

                SUM(
                    CASE
                        WHEN delay_month_count >= 2
                        THEN 1
                        ELSE 0
                    END
                ) AS customers_with_repeated_delay,

                AVG(latest_utilization_ratio) * 100
                    AS average_latest_utilization_pct,

                SUM(
                    CASE
                        WHEN latest_utilization_ratio > 1
                        THEN 1
                        ELSE 0
                    END
                ) AS over_limit_customers,

                SUM(total_bill_amount_6m)
                    AS total_bill_amount_6m,

                SUM(total_payment_amount_6m)
                    AS total_payment_amount_6m

            FROM credit_profiles
        """

        cursor.execute(query)
        row = cursor.fetchone()

        return {
            "total_customers":
                int(row["total_customers"]),

            "total_credit_exposure":
                float(row["total_credit_exposure"]),

            "average_credit_limit":
                round(float(row["average_credit_limit"]), 2),

            "historical_defaults":
                int(row["historical_defaults"]),

            "historical_default_rate_pct":
                round(
                    float(row["historical_default_rate_pct"]),
                    2
                ),

            "customers_with_payment_delay":
                int(row["customers_with_payment_delay"]),

            "customers_with_repeated_delay":
                int(row["customers_with_repeated_delay"]),

            "average_latest_utilization_pct":
                round(
                    float(row["average_latest_utilization_pct"]),
                    2
                ),

            "over_limit_customers":
                int(row["over_limit_customers"]),

            "total_bill_amount_6m":
                float(row["total_bill_amount_6m"]),

            "total_payment_amount_6m":
                float(row["total_payment_amount_6m"])
        }

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_risk_distribution():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                r.risk_band,
                COUNT(*) AS total_customers,
                SUM(cp.default_next_month)
                    AS historical_defaults,
                AVG(cp.default_next_month) * 100
                    AS historical_default_rate_pct,
                AVG(r.risk_score)
                    AS average_risk_score

            FROM customer_risk_assessment r

            INNER JOIN credit_profiles cp
                ON r.customer_id = cp.customer_id

            GROUP BY r.risk_band

            ORDER BY FIELD(
                r.risk_band,
                'LOW',
                'MEDIUM',
                'HIGH'
            )
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            row["total_customers"] = int(
                row["total_customers"]
            )

            row["historical_defaults"] = int(
                row["historical_defaults"]
            )

            row["historical_default_rate_pct"] = round(
                float(row["historical_default_rate_pct"]),
                2
            )

            row["average_risk_score"] = round(
                float(row["average_risk_score"]),
                2
            )

        return rows

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_monthly_trends():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                activity_month,

                COUNT(*) AS customer_records,

                SUM(bill_amount)
                    AS total_bill_amount,

                AVG(bill_amount)
                    AS average_bill_amount,

                SUM(payment_amount)
                    AS total_payment_amount,

                AVG(payment_amount)
                    AS average_payment_amount,

                SUM(
                    CASE
                        WHEN repayment_status > 0
                        THEN 1
                        ELSE 0
                    END
                ) AS delayed_customers,

                AVG(
                    CASE
                        WHEN repayment_status > 0
                        THEN 1
                        ELSE 0
                    END
                ) * 100 AS delayed_customer_rate_pct

            FROM monthly_credit_activity

            GROUP BY activity_month

            ORDER BY activity_month
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            row["total_bill_amount"] = float(
                row["total_bill_amount"]
            )

            row["average_bill_amount"] = round(
                float(row["average_bill_amount"]),
                2
            )

            row["total_payment_amount"] = float(
                row["total_payment_amount"]
            )

            row["average_payment_amount"] = round(
                float(row["average_payment_amount"]),
                2
            )

            row["delayed_customers"] = int(
                row["delayed_customers"]
            )

            row["delayed_customer_rate_pct"] = round(
                float(row["delayed_customer_rate_pct"]),
                2
            )

        return rows

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_segment_analytics(segment: str):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        segment_config = {
            "gender": {
                "select": "g.gender_name",
                "joins": """
                    INNER JOIN dim_gender g
                        ON c.gender_code = g.gender_code
                """
            },

            "education": {
                "select": "e.education_name",
                "joins": """
                    INNER JOIN dim_education e
                        ON c.education_code = e.education_code
                """
            },

            "marital_status": {
                "select": "m.marital_status_name",
                "joins": """
                    INNER JOIN dim_marital_status m
                        ON c.marital_status_code =
                           m.marital_status_code
                """
            },

            "age": {
                "select": """
                    CASE
                        WHEN c.age BETWEEN 21 AND 29
                            THEN '21-29'
                        WHEN c.age BETWEEN 30 AND 39
                            THEN '30-39'
                        WHEN c.age BETWEEN 40 AND 49
                            THEN '40-49'
                        WHEN c.age BETWEEN 50 AND 59
                            THEN '50-59'
                        ELSE '60+'
                    END
                """,
                "joins": ""
            }
        }

        config = segment_config[segment]

        query = f"""
            SELECT
                {config["select"]} AS segment,

                COUNT(*) AS total_customers,

                AVG(cp.credit_limit)
                    AS average_credit_limit,

                SUM(cp.default_next_month)
                    AS historical_defaults,

                AVG(cp.default_next_month) * 100
                    AS historical_default_rate_pct,

                SUM(cp.has_payment_delay)
                    AS customers_with_payment_delay,

                AVG(cp.latest_utilization_ratio) * 100
                    AS average_latest_utilization_pct

            FROM customers c

            INNER JOIN credit_profiles cp
                ON c.customer_id = cp.customer_id

            {config["joins"]}

            GROUP BY {config["select"]}

            ORDER BY total_customers DESC
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        for row in rows:

            row["total_customers"] = int(
                row["total_customers"]
            )

            row["average_credit_limit"] = round(
                float(row["average_credit_limit"]),
                2
            )

            row["historical_defaults"] = int(
                row["historical_defaults"]
            )

            row["historical_default_rate_pct"] = round(
                float(
                    row[
                        "historical_default_rate_pct"
                    ]
                ),
                2
            )

            row["customers_with_payment_delay"] = int(
                row["customers_with_payment_delay"]
            )

            row["average_latest_utilization_pct"] = round(
                float(
                    row[
                        "average_latest_utilization_pct"
                    ]
                ),
                2
            )

        return rows

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()