# PeoplePulse - Complete Setup and Run Instructions

## Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm (install with: `npm install -g pnpm`)
- Git

## Step 1: Backend Setup

### 1.1 Navigate to backend directory
```bash
cd backend
```

### 1.2 Install Python dependencies
```bash
python -m pip install -r requirements.txt
```

### 1.3 Create .env file
```bash
copy .env.example .env
```

### 1.4 Set database URL (for local development with SQLite)
```powershell
$env:DATABASE_URL="sqlite:///./peoplepulse.db"
```

### 1.5 Run database migrations
```powershell
$env:DATABASE_URL="sqlite:///./peoplepulse.db"; alembic upgrade head
```

### 1.6 Seed reference data
```powershell
$env:DATABASE_URL="sqlite:///./peoplepulse.db"; python ../database/seed_reference_data.py
```

### 1.7 Generate synthetic data
```powershell
cd ..
python scripts/generate_data.py --seed 20261022 --mode small
```

### 1.8 Load generated data into database
```powershell
$env:DATABASE_URL="sqlite:///./backend/peoplepulse.db"; python database/load_generated_data.py
```

### 1.9 Run backend tests (optional but recommended)
```powershell
cd backend
$env:DATABASE_URL="sqlite:///./peoplepulse.db"; python -m pytest tests/unit/ -v
```

### 1.10 Start backend server
```powershell
$env:DATABASE_URL="sqlite:///./peoplepulse.db"; uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

## Step 2: Frontend Setup

### 2.1 Navigate to frontend directory
```bash
cd frontend
```

### 2.2 Create .env.local file
```bash
copy .env.example .env.local
```

### 2.3 Install dependencies
```bash
pnpm install
```

**If network issues occur**, try:
```bash
pnpm config set registry https://registry.npmmirror.com
pnpm install
pnpm config set registry https://registry.npmjs.org
```

### 2.4 Run type-check (optional)
```bash
pnpm run type-check
```

### 2.5 Run lint (optional)
```bash
pnpm run lint
```

### 2.6 Start frontend development server
```bash
pnpm run dev
```

Frontend will be available at: http://localhost:3000

## Step 3: Access the Application

### 3.1 Open browser
Navigate to: http://localhost:3000

### 3.2 Login with demo credentials
- **Email:** admin@peoplepulse.demo
- **Password:** PeoplePulse2026!

### 3.3 Explore the application
- **Dashboard:** View KPIs and charts
- **Goals:** Manage goals and key results
- **Check-ins:** Submit and view check-ins
- **Reviews:** Performance reviews
- **Feedback:** Peer and manager feedback
- **Development Plans:** Professional development tracking
- **Issues:** View data quality issues and anomalies
- **Audit:** Audit history
- **Settings:** Generate data and view validation reports

## Quick Start (All-in-One Script)

For Windows PowerShell, save this as `start.ps1`:

```powershell
# Set database URL
$env:DATABASE_URL="sqlite:///./backend/peoplepulse.db"

# Backend setup
cd backend
python -m pip install -r requirements.txt -q
alembic upgrade head
python ../database/seed_reference_data.py
cd ..
python scripts/generate_data.py --seed 20261022 --mode small
python database/load_generated_data.py

# Start backend (in background)
cd backend
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "app.main:app", "--host", "0.0.0.0", "--port", "8000"

# Frontend setup
cd ../frontend
pnpm install
pnpm run dev
```

## Docker Setup (Alternative)

If Docker is available and running:

### 1. Start all services
```bash
docker compose up -d
```

### 2. Run migrations
```bash
docker compose exec backend alembic upgrade head
```

### 3. Seed data
```bash
docker compose exec backend python database/seed_reference_data.py
```

### 4. Generate data
```bash
docker compose exec backend python scripts/generate_data.py --seed 20261022 --mode small
```

### 5. Load data
```bash
docker compose exec backend python database/load_generated_data.py
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify DATABASE_URL is set correctly
- Check Python dependencies are installed

### Frontend won't start
- Check if port 3000 is already in use
- Verify node_modules exists (run `pnpm install`)
- Check .env.local file exists

### Database errors
- Ensure migrations were run: `alembic upgrade head`
- Verify database file exists at `backend/peoplepulse.db`
- Check DATABASE_URL environment variable

### Network issues with pnpm
- Try using npm mirror: `pnpm config set registry https://registry.npmmirror.com`
- Or use npm directly: `npm install`
- Wait for network to stabilize and retry

## API Endpoints

Once backend is running, test these endpoints:

- Health check: http://localhost:8000/api/v1/health
- Dashboard: http://localhost:8000/api/v1/dashboard
- Goals: http://localhost:8000/api/v1/goals
- Employees: http://localhost:8000/api/v1/employees
- Reviews: http://localhost:8000/api/v1/reviews
- Check-ins: http://localhost:8000/api/v1/check-ins
- Feedback: http://localhost:8000/api/v1/feedback
- Development plans: http://localhost:8000/api/v1/development-plans
- Issues: http://localhost:8000/api/v1/issues
- Audit: http://localhost:8000/api/v1/audit

## Stopping the Application

### Stop backend
Press `Ctrl+C` in the terminal where uvicorn is running

### Stop frontend
Press `Ctrl+C` in the terminal where `pnpm run dev` is running

### Stop Docker services
```bash
docker compose down
```

## Data Management

### Regenerate data
```powershell
$env:DATABASE_URL="sqlite:///./backend/peoplepulse.db"
python scripts/generate_data.py --seed 20261022 --mode small
python database/load_generated_data.py
```

### Clear database
```powershell
del backend\peoplepulse.db
$env:DATABASE_URL="sqlite:///./peoplepulse.db"; alembic upgrade head
```

### Run validation
```powershell
python scripts/validate_data.py
```

### Run anomaly evaluation
```powershell
python scripts/evaluate_anomalies.py
```
