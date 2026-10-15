# PrintFlow - DBMS Project 69

Printing Press Job Order and Production Management System

**Student:** Om Pilaji | **Roll number:** 25WU0102202 | **University:** Woxsen University

## What is included
- React/Vite responsive management dashboard (`frontend/`)
- FastAPI backend with SQLAlchemy ORM (`backend/`)
- SQLite zero-configuration demonstration; PostgreSQL supported by `DATABASE_URL`
- Complete lifecycle: customers, quotations, job orders, stock issue, machine schedules, production stages, deliveries, invoices and payments
- SQL reference schema and reporting queries (`database/`)
- Academic report PDF and editable DOCX (`report/`)

## Local run - Windows PowerShell
Open two separate terminals in the extracted folder.

### Terminal 1: Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
If activation is blocked, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`.

### Terminal 2: Frontend
```powershell
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 . Backend API docs at http://localhost:8000/docs

## PostgreSQL (recommended for DBMS review)
Create database `printing_press_db` in pgAdmin. Set environment variable in the backend terminal before starting:
```powershell
$env:DATABASE_URL="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/printing_press_db"
uvicorn main:app --reload --port 8000
```
The SQLAlchemy models create the necessary tables automatically. In the PgAdmin Query Tool, run `database/reports.sql` only after the backend has created the tables. Do not include the password in screenshots or Git.

## Demo walkthrough
1. Dashboard > Load sample master data
2. Customers > create or inspect customer IDs
3. Quotations > create quotation for an existing customer ID
4. Jobs > create job; optional quotation ID must belong to same customer
5. Issues > issue stock from an existing material for an existing job
6. Schedules > select job, machine, start and end timestamps; overlaps are rejected
7. Stages > record DESIGN, PREPRESS, PRINTING, FINISHING, PACKING in order as DONE
8. Deliveries > record a partial or complete delivery (cannot exceed ordered quantity)
9. Invoices > create one invoice per job, then Payments > record valid payment
10. Dashboard > inspect pending jobs, low stock, revenue and outstanding balances

## Scope and limitations
This is a newly built course-project implementation, not a recovered copy of the earlier 29-table project. It has 11 relational tables, core validated transactions and a report. The report does **not** claim previously reported 28 database tests were run on this new codebase. For full production use add authentication, role management, migrations, backup automation, stage-edit endpoints, partial reservation logic and database-level PostgreSQL EXCLUDE scheduling constraints. Machine conflict checks in this demonstration operate in application logic and are not concurrency-safe without DB-level exclusion constraints.
