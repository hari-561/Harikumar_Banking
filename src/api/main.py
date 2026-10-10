from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.auth import router as auth_router
from src.api.routes.customers import (
    router as customers_router
)
from src.api.routes.analytics import (
    router as analytics_router
)
from src.api.routes.export import (
    router as export_router
)
app = FastAPI(
    title="Banking Loan Risk Analysis API",
    description=(
        "REST API for customer credit profiles, "
        "repayment behaviour, risk assessments, "
        "and portfolio analytics."
    ),
    version="1.0.0"
)


app.include_router(health_router)
app.include_router(health_router)
app.include_router(customers_router)
app.include_router(analytics_router)
app.include_router(export_router)
app.include_router(auth_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Banking Loan Risk Analysis API",
        "status": "running"
    }