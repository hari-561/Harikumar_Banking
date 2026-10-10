from src.api.database import get_db_connection


def get_customers_for_export(
    risk_band=None,
    has_payment_delay=None,
    min_credit_limit=None,
    max_credit_limit=None,
    sort_by="customer_id",
    sort_order="asc"
):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        where_conditions = []
        parameters = []

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
                "WHERE "
                + " AND ".join(where_conditions)
            )

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

        query = f"""
            SELECT
                c.customer_id,

                g.gender_name AS gender,
                e.education_name AS education,
                m.marital_status_name
                    AS marital_status,

                c.age,

                cp.credit_limit,
                cp.delay_month_count,
                cp.max_delay_status,
                cp.has_payment_delay,

                cp.total_bill_amount_6m,
                cp.average_bill_amount_6m,

                cp.total_payment_amount_6m,
                cp.average_payment_amount_6m,

                cp.latest_utilization_ratio,

                r.payment_to_bill_ratio,

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

            {where_clause}

            ORDER BY
                {sort_column} {sql_sort_order},
                c.customer_id ASC
        """

        cursor.execute(
            query,
            tuple(parameters)
        )

        return cursor.fetchall()

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()