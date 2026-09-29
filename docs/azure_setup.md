# Azure setup (portal names may differ slightly; follow the current UI)

## 0. Account and budget
1. Sign up for **Azure for Students** with a personal Microsoft account and verify student status.
   It provides $100 credit (valid 12 months) with no credit card; services stop when credit runs out.
2. In **Cost Management > Budgets**, add a budget with email alerts at 50% and 80%.
3. Put everything in ONE resource group (e.g. `rg-frp`) so you can delete it all at the end.

## 1. Storage (ADLS Gen2)
- Create a Storage account in a nearby region (e.g. North/West Europe) with **Hierarchical namespace** enabled, Standard, LRS.
- Containers `curated` and `gold` are created automatically by `upload_adls.py`.
- Copy the **connection string** (Access keys) into `.env` as `AZURE_STORAGE_CONNECTION_STRING`.

## 2. Azure SQL Database
- Create a SQL server (SQL authentication) and a database. Prefer a **serverless / auto-pause** option or the smallest tier.
  Check whether a free database offer is currently available for your subscription.
- **Networking:** add a firewall rule for your current public IP. Keep "Allow Azure services" off unless needed.
- Put server name, database, user and password into `.env` (`AZURE_SQL_*`).
- Install **ODBC Driver 18 for SQL Server** on your machine (needed by `pyodbc`).

## 3. Run
```bash
python -m frp.run_all --feature-set conservative --upload
```
Watch Cost Management after the first load. Loading millions of rows through SQL is slow; use `MAX_STEP` or `LOAD_SCOPE=test_period` if needed.

## 4. Power BI
Connect to the database (Azure SQL Database connector, **Import** mode). See `dashboard/README.md`.

## 5. Clean up
When done and screenshots/recording are captured, delete the resource group (or pause/delete the database).
Never commit `.env`, keys, or connection strings. If a secret ever lands in git history, rotate it.
