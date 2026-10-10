# Banking Loan Risk Analysis Application

A full-stack banking credit risk analytics application developed using **Python, Pandas, MySQL, FastAPI, and Streamlit**.

The application processes historical credit card repayment data, applies transparent business rules to classify customer credit risk, and provides interactive dashboards, customer management, portfolio analytics, and downloadable reports.

This project is a **rule-based analytics system without machine learning or generative AI**.

## 1. Project Overview

Banks and financial institutions need reliable tools to monitor credit exposure, repayment behaviour, and customer risk.

This application provides an end-to-end data engineering and analytics workflow that transforms raw customer credit data into structured, actionable insights.

### Key Capabilities

- Data extraction, validation, cleaning, and transformation
- Incremental ETL with change detection and batch auditing
- MySQL relational database with integrity constraints and indexes
- Rule-based credit risk scoring and classification
- Portfolio KPIs and customer segmentation
- REST APIs for customer data, analytics, and exports
- Customer creation, updating, and deletion
- JWT authentication and role-based access control
- Interactive Streamlit dashboards
- CSV reporting and filtered exports
- Structured application logging
- Automated testing and integration verification

## 2. Technology Stack

| Layer | Technologies |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas, NumPy |
| Database | MySQL |
| Backend | FastAPI, Pydantic, Uvicorn |
| Frontend | Streamlit, Plotly |
| Authentication | JWT, Argon2 password hashing |
| Testing | Pytest, pytest-cov |
| Version Control | Git, GitHub |

## 3. System Architecture

The application follows a layered architecture:

```text
UCI Credit Card Default Dataset
              |
              v
    Data Extraction (Pandas)
              |
              v
    Data Quality Validation
              |
              v
    Data Transformation
              |
              v
      Incremental ETL
              |
              v
       MySQL Database
              |
       +------+------+
       |             |
       v             v
  Risk Rules     SQL Analytics
       |             |
       +------+------+
              |
              v
        FastAPI REST API
              |
        JWT Authentication
        Role-Based Access
              |
              v
      Streamlit Application
              |
    Dashboards / CRUD / Reports
```

The frontend communicates with the FastAPI backend through HTTP requests. The backend retrieves and updates data stored in MySQL.

## 4. Dataset

**Dataset:** Default of Credit Card Clients

**Source:** UCI Machine Learning Repository

The dataset contains 30,000 customer records and 25 fields, including the customer identifier and historical default outcome.

The information includes:

- Customer demographic attributes
- Credit limits
- Six months of repayment status
- Six months of bill statement amounts
- Six months of payment amounts
- Historical default outcome for the following month

The source file is located at:

`data/raw/default_of_credit_card_clients.xls`

The historical default field is used to evaluate observed default rates, not as an input to the rule-based risk score.

## 5. ETL Pipeline

The ETL implementation is organized into separate Python modules under `etl/`.

### Extraction

The extraction module reads the Excel source dataset and validates the presence of required columns.

### Data Quality Validation

The validation process checks data integrity, including missing values, duplicate customer identifiers, invalid credit limits, invalid demographic codes, and repayment status values.

Undocumented demographic category codes are handled through defined mappings while preserving the original information.

### Transformation

The transformation stage prepares standardized customer attributes and derives analytical features such as:

- Number of delayed repayment months
- Maximum repayment delay status
- Payment delay indicator
- Total and average bill amounts over six months
- Total and average payments over six months
- Latest credit utilization ratio

### Database Loading

Curated data is loaded into relational MySQL tables with primary keys, foreign keys, validation constraints, and indexes.

### Incremental Processing

The incremental pipeline identifies new, changed, and unchanged records.

Batch execution information is maintained in `etl_batch_audit`, including record counts, processing status, timestamps, and errors.

## 6. Database Design

The database is named `banking_loan_db`.

Its principal tables include:

| Table | Purpose |
|---|---|
| `customers` | Customer demographic information |
| `credit_profiles` | Credit exposure and engineered behavioural features |
| `monthly_credit_activity` | Monthly repayment, billing, and payment records |
| `customer_risk_assessment` | Risk scores, bands, and rule versions |
| `etl_batch_audit` | Incremental ETL execution history |
| `app_users` | Application accounts and roles |
| `dim_gender` | Gender reference values |
| `dim_education` | Education reference values |
| `dim_marital_status` | Marital status reference values |

Database definitions are maintained in:

- `database/schema.sql`
- `database/analytics_queries.sql`

The initial dataset contains 30,000 customers and six monthly activity records per customer, corresponding to 180,000 historical monthly records.

## 7. Rule-Based Credit Risk Analysis

The application uses a transparent, deterministic scoring methodology.

Four behavioural indicators contribute to the final risk score:

| Indicator | Maximum Points |
|---|---:|
| Repayment delay frequency | 3 |
| Maximum delay severity | 3 |
| Latest credit utilization | 3 |
| Six-month payment behaviour | 2 |
| **Total** | **11** |

### Risk Classification

| Score | Risk Band |
|---|---|
| 0–2 | LOW |
| 3–5 | MEDIUM |
| 6–11 | HIGH |

### Historical Evaluation

The initial 30,000-customer dataset produced the following documented results:

| Risk Band | Customers | Historical Default Rate |
|---|---:|---:|
| LOW | 13,966 | 12.61% |
| MEDIUM | 9,673 | 16.62% |
| HIGH | 6,361 | 51.36% |

The overall historical default rate was 22.12%.

These results describe historical observations for the source dataset. They are not model predictions or guarantees of future outcomes.

Detailed scoring rules and evaluation results are documented in [Risk Methodology](docs/risk_methodology.md).

## 8. REST API

The backend is implemented using FastAPI.

### Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/login` | Authenticate a user |
| GET | `/auth/me` | Retrieve the authenticated user's information |

### Customers

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/customers` | List customers with filtering, pagination, and sorting |
| GET | `/customers/{customer_id}` | Retrieve customer details |
| GET | `/customers/{customer_id}/activity` | Retrieve monthly credit activity |
| GET | `/customers/{customer_id}/risk` | Retrieve the customer's risk assessment |
| POST | `/customers` | Create a customer |
| PUT | `/customers/{customer_id}` | Update a customer |
| DELETE | `/customers/{customer_id}` | Delete a customer |

### Analytics

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/analytics/summary` | Portfolio summary |
| GET | `/analytics/risk-distribution` | Risk band distribution |
| GET | `/analytics/monthly-trends` | Monthly credit trends |
| GET | `/analytics/segments` | Demographic segment analytics |

### Export and Health

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/export/customers` | Export filtered customer records as CSV |
| GET | `/health` | Check API and database availability |

Interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

## 9. Authentication and Authorization

The application implements JWT-based authentication and role-based access control.

Passwords are protected using Argon2 hashing.

### Application Roles

| Role | Permissions |
|---|---|
| ADMIN | View analytics, manage customers, and export data |
| ANALYST | View analytics and export data |
| VIEWER | View authorized customer and analytics information |

Protected endpoints validate the user's access token and assigned role.

The backend enforces authorization independently of frontend navigation.

## 10. Streamlit Dashboard

The frontend provides six application sections.

### Portfolio Overview

Displays high-level portfolio KPIs, credit exposure, customer distribution, and historical default information.

### Risk Analysis

Presents rule-based credit risk bands, scoring information, and comparisons with historical default outcomes.

### Portfolio Analytics

Supports analysis of repayment behaviour, credit utilization, monthly trends, and customer segments.

### Customer Explorer

Allows users to search, filter, sort, and inspect customer profiles, credit activity, and risk assessments.

### Customer Management

Provides authorized customer creation, updating, and deletion workflows.

### Reports & Export

Offers portfolio reporting, segmentation insights, and filtered CSV exports.

## 11. Project Structure

```text
banking_loan/
|
|-- data/
|   `-- raw/
|
|-- database/
|   |-- schema.sql
|   `-- analytics_queries.sql
|
|-- docs/
|   |-- kpi_definitions.md
|   `-- risk_methodology.md
|
|-- etl/
|   |-- extract.py
|   |-- validate.py
|   |-- transform.py
|   |-- load.py
|   |-- incremental.py
|   |-- incremental_load.py
|   `-- prepare_tables.py
|
|-- rules/
|   |-- risk_rules.py
|   `-- load_risk.py
|
|-- src/
|   |-- api/
|   |   |-- routes/
|   |   |-- services/
|   |   |-- security/
|   |   `-- main.py
|   |
|   |-- frontend/
|   |   |-- components/
|   |   |-- pages/
|   |   `-- app.py
|   |
|   `-- utils/
|
|-- tests/
|
|-- .env.example
|-- requirements.txt
`-- README.md
```

## 12. Installation and Setup

### Prerequisites

- Python with support for the versions in `requirements.txt`
- MySQL Server
- Git
- A terminal or development environment such as VS Code

### Clone the Repository

```powershell
git clone https://github.com/hari-561/Harikumar_Banking.git
cd Harikumar_Banking
```

### Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as the template.

Configure the MySQL connection and JWT settings:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=banking_loan_db

JWT_SECRET_KEY=replace_with_a_secure_random_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

API_BASE_URL=http://127.0.0.1:8000
```

The JWT secret must be a secure random value containing at least 32 characters.

Never commit actual database credentials or JWT secrets.

### Initialize the Database

The database schema is defined in `database/schema.sql`.

For a fresh database, execute this SQL script using MySQL Workbench or the MySQL command-line client.

The application requires its customer, credit activity, and risk assessment data to be loaded before the dashboards can display portfolio information.

### Create the Initial Administrator

After initializing the database, run:

```powershell
python -m src.api.security.create_admin
```

Follow the prompts to configure the initial administrator account.

### Start the Backend

From the project root:

```powershell
python -m uvicorn src.api.main:app --reload --port 8000
```

Open:

- API root: `http://127.0.0.1:8000/`
- API documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/health`

### Start the Frontend

Open a separate terminal in the project root:

```powershell
python -m streamlit run src/frontend/app.py
```

Open the local Streamlit address displayed in the terminal, typically:

`http://localhost:8501`

Sign in using a configured application account.

## 13. Testing

The project includes automated tests for:

- ETL validation and transformation
- Incremental processing and database loading
- API request validation
- Customer management
- Authentication and JWT handling
- Role-based access control
- Analytics and exports
- Frontend components and navigation
- Error handling and structured logging

### Run Automated Tests

```powershell
python -m pytest tests -q --tb=short
```

### Generate Frontend Coverage

```powershell
python -m pytest tests --cov=src.frontend --cov-report=term-missing:skip-covered -q
```

### Latest Verified Regression Result

- 672 tests passed
- 4 subtests passed
- 1 warning
- 0 failures
- Execution time: 23.00 seconds

Previously verified frontend statement coverage: approximately 83%.

Some integration tests require the backend to be running and appropriate test credentials to be configured.

## 14. Logging and Error Handling

The application uses structured logging for important operations, including:

- ETL execution
- Database connection failures
- Authentication events
- Customer management operations
- API requests
- Processing errors

API validation and exception handling provide controlled responses for invalid requests, missing resources, authorization failures, and unavailable services.

## 15. Documentation

Additional technical documentation:

- [KPI Definitions](docs/kpi_definitions.md)
- [Risk Scoring Methodology](docs/risk_methodology.md)
- [Database Schema](database/schema.sql)
- [Analytics SQL Queries](database/analytics_queries.sql)

Additional architecture, design, and submission documents will be prepared as part of project finalization.

## 16. Limitations and Intended Use

This application is an educational banking data engineering and analytics project.

Risk classifications are generated from predefined behavioural rules and historical credit information. They should not be interpreted as probabilities of default, machine-learning predictions, or automated lending decisions.

The source dataset is historical, and observed default rates may not generalize to other portfolios.

## 17. Repository

**GitHub:** https://github.com/hari-561/Harikumar_Banking

**Project:** Banking Loan Risk Analysis Application

**Category:** Python Full-Stack Development and Data Engineering Capstone
