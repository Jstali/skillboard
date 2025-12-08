# Quick Fix for Template Upload Error

## Problem
The backend is still trying to connect to the Docker hostname "postgres" instead of "localhost".

## Solution

### Step 1: Stop the Current Backend
In the terminal where `uvicorn` is running, press **Ctrl+C** to stop it.

### Step 2: Restart with Correct Database URL

**Option A - Using the helper script:**
```bash
cd backend
./run_local_postgres.sh
```

**Option B - Manual command:**
```bash
cd backend
export DATABASE_URL=postgresql://skillboard:skillboard@localhost:5432/skillboard
uvicorn app.main:app --reload
```

### Step 3: Verify
You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 4: Test
1. Refresh your browser
2. Go to Admin Dashboard → Skills tab
3. Scroll to "Template Files" section
4. Try uploading a file (.xlsx, .csv, or .ods)

## What This Does
- Connects backend to the PostgreSQL container running on localhost:5432
- Automatically creates the `skill_templates` table
- Enables the template upload feature

## Troubleshooting
If you still get errors:
1. Check PostgreSQL is running: `docker ps | grep skillboard-postgres`
2. Check backend logs for specific error messages
3. Verify DATABASE_URL is set: `echo $DATABASE_URL`
