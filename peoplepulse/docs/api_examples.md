# API examples

Base URL: `http://localhost:8000`

## Health

```bash
curl http://localhost:8000/api/v1/health
```

## Demo login

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@peoplepulse.demo","password":"PeoplePulse2026!"}'
```

## Dashboard (live KPIs)

```bash
curl http://localhost:8000/api/v1/dashboard
```

## Create a goal with key results

```bash
curl -X POST http://localhost:8000/api/v1/goals \
  -H "Content-Type: application/json" \
  -d '{
    "employee_employee_id":"EMP-000001",
    "cycle_cycle_id":"CYCLE-2026-H1",
    "title":"Ship H1 outcomes",
    "status":"active",
    "key_results":[
      {"title":"Features","metric_type":"count","target":10,"actual":8,"weight":0.6},
      {"title":"Tests","metric_type":"count","target":20,"actual":15,"weight":0.4}
    ]
  }'
```

Expected `progress_percentage` is 78 when both KRs are valid.

## Check-in with evidence

```bash
curl -X POST http://localhost:8000/api/v1/goals/GOAL-EMP-000001-001/check-ins \
  -H "Content-Type: application/json" \
  -d '{
    "employee_employee_id":"EMP-000001",
    "goal_goal_id":"GOAL-EMP-000001-001",
    "check_in_date":"2026-03-01",
    "notes":"On track",
    "progress_snapshot":{"KR-GOAL-EMP-000001-001-01":9},
    "evidence":[{"title":"Sprint review","url":"https://example.com/evd","evidence_type":"url"}]
  }'
```

Interactive OpenAPI: `/docs`.
