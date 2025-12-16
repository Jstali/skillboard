"""FastAPI main application."""
# Load environment variables from .env file
import os
from pathlib import Path

# Try to load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    print(f"[STARTUP] Loading .env from {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())
    print(f"[STARTUP] HRMS_BASE_URL = {os.environ.get('HRMS_BASE_URL', 'NOT SET')}")
    print(f"[STARTUP] HRMS_INTEGRATION_EMAIL = {os.environ.get('HRMS_INTEGRATION_EMAIL', 'NOT SET')}")
else:
    print(f"[STARTUP] No .env file found at {env_path}")

# Trigger reload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.api import skills, userskills, search, admin, auth, admin_users, admin_employee_skills, admin_dashboard, teams, bands, categories, learning, role_requirements, templates, admin_template_assignments, employee_assignments, skill_gap_analysis, projects, capability_owners, org_structure, level_movement, audit_logs, role_dashboard, hrms, skill_board, metrics, reconciliation, lm_dashboard, dm_dashboard

app = FastAPI(
    title="Skillboard API",
    description="Drag-and-drop skill manager with admin Excel upload, fuzzy search, and user authentication",
    version="2.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:2607", "http://149.102.158.71:2607"],  # Vite default port and server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(userskills.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(admin_users.router)
app.include_router(admin_employee_skills.router)
app.include_router(admin_dashboard.router)
app.include_router(teams.router)
app.include_router(bands.router)
app.include_router(categories.router)

app.include_router(learning.router)
app.include_router(role_requirements.router)
app.include_router(templates.router)
app.include_router(admin_template_assignments.router)
app.include_router(employee_assignments.router)
app.include_router(skill_gap_analysis.router)

# HRMS Pre-Integration routers
app.include_router(projects.router)
app.include_router(capability_owners.router)
app.include_router(org_structure.router)
app.include_router(level_movement.router)
app.include_router(audit_logs.router)
app.include_router(role_dashboard.router)




app.include_router(hrms.router)

# Line Manager Dashboard
app.include_router(lm_dashboard.router)

# Delivery Manager Dashboard
app.include_router(dm_dashboard.router)

# Skill Board Views routers
app.include_router(skill_board.router)
app.include_router(metrics.router)
app.include_router(reconciliation.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    database.init_db()


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Skillboard API", "version": "1.0.0"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

