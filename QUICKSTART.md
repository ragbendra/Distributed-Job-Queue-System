# 🚀 Quick Start Guide - Distributed Job Queue System

## Prerequisites Check

Before starting, ensure you have:
- ✅ Docker Desktop installed
- ✅ Docker Desktop is **RUNNING** (check system tray)
- ✅ At least 4GB RAM available for Docker
- ✅ Ports available: 5432, 5672, 6379, 8000, 3000, 15672

## Step-by-Step Startup

### 1. Start Docker Desktop

**IMPORTANT**: Docker Desktop must be running before you can start the services.

- Look for the Docker icon in your system tray (bottom-right of Windows taskbar)
- If Docker Desktop is not running, start it from the Start menu
- Wait until Docker Desktop shows "Engine running" status

### 2. Navigate to Project Directory

```powershell
cd "C:\Users\Ragha\Downloads\Project(A)\distributed-job-queue"
```

### 3. Start All Services

```powershell
docker-compose up -d
```

This will:
- Pull required Docker images (first time only, ~5 minutes)
- Start PostgreSQL, RabbitMQ, Redis
- Start API, Workers (3 instances), Scheduler, Dashboard
- Create networks and volumes

### 4. Wait for Services to Be Ready

```powershell
# Check service status
docker-compose ps

# Watch logs (Ctrl+C to exit)
docker-compose logs -f
```

Wait until you see:
- ✅ PostgreSQL: "database system is ready to accept connections"
- ✅ RabbitMQ: "Server startup complete"
- ✅ API: "Application startup complete"
- ✅ Workers: "Worker worker-X starting..."

This typically takes **30-60 seconds**.

### 5. Access the Services

Once all services are healthy:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000 | None |
| **API Docs** | http://localhost:8000/docs | None |
| **RabbitMQ UI** | http://localhost:15672 | admin / admin123 |

### 6. Submit Test Jobs

Open a new PowerShell window:

```powershell
cd "C:\Users\Ragha\Downloads\Project(A)\distributed-job-queue"
python scripts/submit_test_jobs.py
```

This will submit 11 test jobs (emails, videos, web scraping).

### 7. Monitor Execution

**Option A: Dashboard** (Recommended)
- Open http://localhost:3000
- Watch jobs move from pending → running → completed
- See retry attempts for failed jobs
- Monitor dead letter queue

**Option B: Logs**
```powershell
# Watch worker logs
docker-compose logs -f worker

# Watch API logs
docker-compose logs -f api

# Watch all logs
docker-compose logs -f
```

**Option C: RabbitMQ UI**
- Open http://localhost:15672
- Login: admin / admin123
- Click "Queues" tab to see message counts

## Common Commands

### View Running Services
```powershell
docker-compose ps
```

### Stop All Services
```powershell
docker-compose down
```

### Stop and Remove All Data
```powershell
docker-compose down -v
```

### Restart a Specific Service
```powershell
docker-compose restart worker
```

### Scale Workers
```powershell
docker-compose up -d --scale worker=5
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 worker
```

### Access Database
```powershell
docker-compose exec postgres psql -U jobqueue -d jobqueue_db
```

Example queries:
```sql
-- Count jobs by status
SELECT status, COUNT(*) FROM jobs GROUP BY status;

-- View recent jobs
SELECT job_type, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;

-- View dead letters
SELECT * FROM dead_letters;
```

## Testing the System

### Test 1: Submit a Simple Job

```powershell
curl -X POST http://localhost:8000/api/v1/jobs `
  -H "Content-Type: application/json" `
  -d '{
    "job_type": "send_email",
    "priority": "high",
    "payload": {
      "to": "test@example.com",
      "subject": "Hello",
      "body": "Test email"
    }
  }'
```

### Test 2: Submit a Job That Will Retry

```powershell
curl -X POST http://localhost:8000/api/v1/jobs `
  -H "Content-Type: application/json" `
  -d '{
    "job_type": "send_email",
    "payload": {
      "to": "test@example.com",
      "subject": "Retry Test",
      "body": "This will fail and retry",
      "failure_rate": 0.8
    },
    "max_retries": 3
  }'
```

Watch it retry with exponential backoff in the logs:
```powershell
docker-compose logs -f worker
```

### Test 3: Create a Scheduled Job

```powershell
curl -X POST http://localhost:8000/api/v1/scheduled-jobs `
  -H "Content-Type: application/json" `
  -d '{
    "name": "hourly-check",
    "job_type": "scrape_website",
    "cron_expression": "0 * * * *",
    "payload": {
      "url": "https://httpbin.org/html",
      "selector": "title"
    },
    "priority": "low"
  }'
```

### Test 4: Check System Statistics

```powershell
curl http://localhost:8000/api/v1/stats
```

## Troubleshooting

### Issue: "docker-compose: command not found"

**Solution**: Docker Desktop is not running or not installed.
1. Start Docker Desktop from the Start menu
2. Wait for it to fully start (green icon in system tray)
3. Try again

### Issue: "port is already allocated"

**Solution**: Another service is using the required ports.
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue: Services keep restarting

**Solution**: Check logs for errors
```powershell
docker-compose logs api
docker-compose logs worker
```

Common causes:
- Database not ready (wait longer)
- RabbitMQ connection failed (check RabbitMQ logs)
- Port conflicts

### Issue: Dashboard shows "Loading..." forever

**Solution**: API is not accessible
1. Check API is running: `docker-compose ps api`
2. Test API directly: `curl http://localhost:8000/health`
3. Check API logs: `docker-compose logs api`

### Issue: Workers not processing jobs

**Solution**: 
1. Check RabbitMQ is running: `docker-compose ps rabbitmq`
2. Check RabbitMQ UI: http://localhost:15672
3. Verify queues exist: Go to "Queues" tab
4. Check worker logs: `docker-compose logs worker`

## Performance Tips

### For Development
- Use 1-2 workers: `docker-compose up -d --scale worker=2`
- Enable hot reload for API changes

### For Testing
- Use 3-5 workers: `docker-compose up -d --scale worker=5`
- Submit batch jobs with test script

### For Production Simulation
- Use 10+ workers: `docker-compose up -d --scale worker=10`
- Monitor resource usage: `docker stats`

## Next Steps

Once everything is running:

1. **Explore the Dashboard** (http://localhost:3000)
   - View real-time statistics
   - Monitor job execution
   - Check dead letter queue

2. **Try the API** (http://localhost:8000/docs)
   - Interactive API documentation
   - Test all endpoints
   - See request/response schemas

3. **Submit Custom Jobs**
   - Modify `scripts/submit_test_jobs.py`
   - Create your own job types
   - Test different scenarios

4. **Monitor RabbitMQ** (http://localhost:15672)
   - View queue depths
   - Monitor message rates
   - Inspect messages

## Stopping the System

### Graceful Shutdown
```powershell
docker-compose down
```

This will:
- Stop all containers gracefully
- Preserve data in volumes
- Keep networks

### Complete Cleanup
```powershell
docker-compose down -v
```

This will:
- Stop all containers
- **DELETE all data** (jobs, database, etc.)
- Remove volumes and networks

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Logs | `docker-compose logs -f` |
| Status | `docker-compose ps` |
| Restart | `docker-compose restart` |
| Scale | `docker-compose up -d --scale worker=5` |

---

**Need Help?** Check the main README.md for detailed documentation.
