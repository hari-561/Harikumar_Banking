import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


load_dotenv()


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "banking_loan_db"),
}


def get_db_connection():
    """
    Create and return a MySQL database connection.
    """

    try:
        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        return connection

    except Error as error:
        raise RuntimeError(
            f"Database connection failed: {error}"
        ) from error