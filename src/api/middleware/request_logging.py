import time

from fastapi import Request

from src.utils.logger import setup_logger


logger = setup_logger("banking.api")


async def log_api_requests(request: Request, call_next):
    """
    Log incoming HTTP requests and their outcomes.
    """

    start_time = time.perf_counter()

    method = request.method
    path = request.url.path

    # Avoid logging query parameters, request bodies,
    # credentials, tokens, or customer data.

    try:
        response = await call_next(request)

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        status_code = response.status_code

        if status_code >= 500:
            log_level = "error"
        elif status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"

        getattr(logger, log_level)(
            "%s %s | status=%s | duration_ms=%.2f",
            method,
            path,
            status_code,
            duration_ms,
        )

        return response

    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.error(
            "%s %s | status=500 | duration_ms=%.2f | "
            "unhandled_exception",
            method,
            path,
            duration_ms,
        )

        raise