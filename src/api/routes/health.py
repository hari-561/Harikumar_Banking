from fastapi import APIRouter, HTTPException

from src.api.database import get_db_connection


router = APIRouter(
    tags=["Health"]
)


@router.get("/health")
def health_check():
    """
    Check API and database availability.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT 1;")
        cursor.fetchone()

        return {
            "status": "healthy",
            "api": "available",
            "database": "connected"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()