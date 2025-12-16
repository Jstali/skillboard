# Skillboard - Drag-and-Drop Skill Manager

A full-stack application for managing employee skills with drag-and-drop interface, Excel upload capabilities, and fuzzy search functionality.

## Features

- **Master Skills List**: Searchable list of all available skills
- **Drag-and-Drop Interface**: Drag skills from master list into "Existing Skills" or "Interested Skills" columns
- **Inline Rating**: Change skill ratings (Beginner/Intermediate/Advanced) directly in the UI
- **Admin Excel Upload**: Upload master skills and employee-skill mappings via Excel/CSV files
- **Fuzzy Search**: Search for employees by skill name with adjustable match threshold
- **Keyboard Accessible**: Full keyboard navigation support for drag-and-drop and rating changes

## Tech Stack

### Frontend
- React 18 + Vite
- TypeScript
- Tailwind CSS
- dnd-kit (drag-and-drop)
- Axios (API calls)

### Backend
- FastAPI (Python)
- SQLAlchemy + Alembic
- PostgreSQL
- RapidFuzz (fuzzy matching)
- Pandas + openpyxl (Excel parsing)

## Project Structure

```
/
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   └── services/      # API service layer
│   └── package.json
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── db/         # Database models and CRUD
│   │   └── main.py     # FastAPI app
│   └── requirements.txt
├── examples/           # Sample Excel files
├── docker-compose.yml # Docker orchestration
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local frontend development)

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project directory**

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Initialize sample data** (optional):
   - First, import users: Use the admin panel at `/admin/users` or run the seed script
   - Upload `examples/skills.xlsx` to populate master skills
   - Upload `examples/employee_skill_mappings.csv` to populate employee skills
   - Check `users_import_report.csv` for temporary passwords (dev only)

### Local Development

#### Backend

1. **Set up Python environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL** (or use Docker):
   ```bash
   docker run -d --name skillboard-postgres \
     -e POSTGRES_USER=skillboard \
     -e POSTGRES_PASSWORD=skillboard \
     -e POSTGRES_DB=skillboard \
     -p 5432:5432 postgres:15-alpine
   ```

3. **Set environment variables**:
   ```bash
   export DATABASE_URL=postgresql://skillboard:skillboard@localhost:5432/skillboard
   ```

4. **Run the backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

#### Frontend

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**:
   ```bash
   npm run dev
   ```

3. **Access the app**: http://localhost:5173

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with email and password (returns JWT token)
- `POST /api/auth/register` - Register new user account
- `GET /api/auth/me` - Get current user information (requires JWT)
- `POST /api/auth/change-password` - Change user password (requires JWT)

### Skills
- `GET /api/skills/` - Get all skills
- `GET /api/skills/{id}` - Get skill by ID
- `POST /api/skills/` - Create a skill

### User Skills (Authenticated)
- `GET /api/user-skills/me` - Get current user's skills (requires JWT)
- `POST /api/user-skills/me` - Create/update skill for current user (requires JWT)
- `PUT /api/user-skills/me/{id}` - Update skill for current user (requires JWT)
- `GET /api/user-skills/employee/{employee_id}` - Get employee skills (public/admin)
- `POST /api/user-skills/` - Create/update employee skill (legacy)
- `PUT /api/user-skills/{id}` - Update employee skill (legacy)

### Search
- `GET /api/search/skills?q={query}&threshold={0-100}&limit={n}` - Fuzzy search employees by skill

### Admin (Requires X-ADMIN-KEY header in dev, JWT admin in production)
- `POST /api/admin/upload-skills` - Upload master skills Excel/CSV
- `POST /api/admin/upload-employee-skills` - Upload employee skills Excel/CSV
- `POST /api/admin/import-users` - Import users from CSV (creates Employee and User records)
- `POST /api/admin/import-employee-skills` - Import employee-skill mappings with fuzzy matching

## Sample API Calls

### Upload Skills
```bash
curl -X POST "http://localhost:8000/api/admin/upload-skills" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@examples/skills.xlsx"
```

### Upload Employee Skills
```bash
curl -X POST "http://localhost:8000/api/admin/upload-employee-skills" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@examples/employee_skills.xlsx"
```

### Fuzzy Search
```bash
curl "http://localhost:8000/api/search/skills?q=react&threshold=75&limit=10"
```

### Get All Skills
```bash
curl "http://localhost:8000/api/skills/"
```

## Excel File Formats

### Master Skills (`skills.xlsx`)
Required columns:
- `name` (required): Skill name
- `description` (optional): Skill description

### Employee Skills (`employee_skills.xlsx`)
Required columns:
- `EmployeeID` (required): Employee identifier
- `EmployeeName` (required): Employee full name
- `SkillName` (required): Name of the skill (must match master skills)
- `Rating` (required): Beginner, Intermediate, or Advanced
- `YearsExperience` (optional): Years of experience with the skill

## Testing

### Backend Tests
```bash
cd backend
pytest tests/test_search.py -v
```

## Environment Variables

See `.env.example` for all available environment variables. Copy it to `.env` and adjust as needed:

```bash
cp .env.example .env
```

## Database Migrations

The application uses SQLAlchemy with automatic table creation on startup. For production, consider using Alembic for proper migrations:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Authentication

The application now includes full JWT-based authentication:

1. **User Registration & Login**: Employees can register or log in with email and password
2. **JWT Tokens**: Secure token-based authentication with configurable expiration
3. **Password Hashing**: Bcrypt password hashing for security
4. **User Management**: Admin can bulk import users via CSV
5. **Protected Routes**: Frontend routes are protected with authentication checks

### Creating an Admin User

To create an admin user or promote an existing user to admin:

**Option 1: Run inside Docker container (Recommended)**
```bash
# Create a new admin user
docker-compose exec backend python -m app.scripts.create_admin --email admin@company.com --password yourpassword

# Promote existing user to admin
docker-compose exec backend python -m app.scripts.create_admin --email existing@company.com --promote
```

**Option 2: Run from host machine**
```bash
# Set database URL for host machine
# Windows PowerShell:
$env:DATABASE_URL="postgresql://skillboard:skillboard@localhost:5433/skillboard"

# Windows CMD:
set DATABASE_URL=postgresql://skillboard:skillboard@localhost:5433/skillboard

# Linux/Mac:
export DATABASE_URL=postgresql://skillboard:skillboard@localhost:5433/skillboard

# Then run the script
cd backend
python -m app.scripts.create_admin --email admin@company.com --password yourpassword
```

After creating/promoting an admin user, you can:
1. Log in at `/login` with the admin email and password
2. Access the HR Dashboard at `/hr/dashboard` or Admin Dashboard at `/admin/dashboard`
3. Import users and skills via the Admin Users page at `/admin/users`

### User Import & Temporary Passwords

**For Development Only:**

1. **Import Users via CSV**:
   ```bash
   # Using the admin endpoint (requires X-ADMIN-KEY header in dev)
   curl -X POST "http://localhost:8000/api/admin/import-users" \
     -H "X-ADMIN-KEY: dev-admin-key-change-in-production" \
     -F "file=@examples/users.csv"
   ```

2. **Or use the seed script**:
   ```bash
   cd backend
   python -m app.scripts.seed_users examples/users.csv
   uvicorn app.main:app
   ```

3. **Get Temporary Passwords**:
   - After import, check `users_import_report.csv` in the backend directory
   - This file contains plaintext temporary passwords (DEV ONLY)
   - In production, passwords should be sent via secure email service

4. **Employee Login Flow**:
   - Employees log in with their company email and temp password
   - On first login, they may be prompted to change password
   - They can then review and map their imported skills

### CSV Import Formats

**users.csv** (required columns):
```csv
employee_id,first_name,last_name,company_email,department,role
E001,Sai,Vaishnav,sai.vaishnav@company.com,Engineering,Developer
```

**employee_skill_mappings.csv** (required columns):
```csv
employee_id,skill_name,rating,years_experience,notes
E001,React,advanced,3,Used in recent projects
```

- `rating` values: `Beginner`, `Intermediate`, or `Advanced`
- `years_experience` and `notes` are optional
- Skills are fuzzy-matched to master skills (match_score >= 90 auto-links, 70-90 flags for review)

## Limitations & Future Enhancements

- **File Upload Limits**: Maximum 10,000 rows per file (configurable in `backend/app/api/admin.py`)
- **Authentication**: JWT-based auth implemented; production should use secure cookie flags and refresh tokens
- **Temporary Passwords**: Currently stored in CSV (dev only); production should use secure email service
- **Pagination**: Skills list uses simple limit/offset (consider cursor-based pagination for large datasets)
- **Real-time Updates**: Consider WebSocket support for collaborative editing
- **Export**: Add ability to export employee skills to Excel
- **Analytics**: Add skill gap analysis and reporting
- **Rate Limiting**: Login endpoint should have rate limiting in production

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `docker ps`
- Check DATABASE_URL environment variable
- Verify network connectivity between services

### Frontend Not Connecting to Backend
- Check CORS settings in `backend/app/main.py`
- Verify API URL in `frontend/src/services/api.ts`
- Check browser console for errors

### Excel Upload Fails
- Verify file format matches expected columns
- Check file size (max 10k rows)
- Review error messages in API response

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

