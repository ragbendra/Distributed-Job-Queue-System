# 📚 Distributed Job Queue System - Complete Technical Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Shared Components](#3-shared-components)
4. [API Service](#4-api-service)
5. [Worker Service](#5-worker-service)
6. [Scheduler Service](#6-scheduler-service)
7. [Dashboard Service](#7-dashboard-service)
8. [Infrastructure Configuration](#8-infrastructure-configuration)
9. [Data Flow Analysis](#9-data-flow-analysis)
10. [Key Concepts Explained](#10-key-concepts-explained)

---

# 1. Project Overview

## 1.1 What Is This Project?

This is a **production-grade distributed job queue system** - an infrastructure component that processes background tasks asynchronously. Instead of executing long-running operations (like sending emails or processing videos) during an HTTP request, the system queues these tasks and processes them separately.

## 1.2 Why Do Backend Systems Need This?

Consider these scenarios:
- **Email sending**: A user signs up → you don't wait 5 seconds for the email API
- **Video processing**: A user uploads a video → you don't make them wait 10 minutes
- **Web scraping**: You need to fetch data from 100 websites → you don't block the request

A job queue allows you to:
1. **Accept the request quickly** (milliseconds)
2. **Queue the work for later** (stored reliably)
3. **Process asynchronously** (workers handle it)
4. **Track progress** (real-time status updates)
5. **Handle failures gracefully** (retry logic, dead letter queue)

## 1.3 Key Features Implemented

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Exponential Backoff** | Retry delays: 2s → 4s → 8s → 16s | Prevents thundering herd problem |
| **Dead Letter Queue** | Captures permanently failed jobs | No job loss, enables analysis |
| **Priority Queues** | High/Medium/Low priority | Critical jobs process first |
| **Scheduled Jobs** | Cron-like recurring tasks | Automate periodic work |
| **Real-time Monitoring** | Dashboard with live updates | Operational visibility |
| **Horizontal Scaling** | Add more workers on demand | Handle load spikes |

## 1.4 Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    TECHNOLOGY STACK                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend    │  React 18, CSS3, Axios                       │
│  Backend     │  Python 3.11, FastAPI, SQLAlchemy            │
│  Database    │  PostgreSQL 15 (persistent storage)          │
│  Message Q   │  RabbitMQ 3.12 (job distribution)            │
│  Cache       │  Redis 7 (real-time status)                  │
│  Container   │  Docker, Docker Compose                      │
└─────────────────────────────────────────────────────────────┘
```

---

# 2. Architecture Deep Dive

## 2.1 System Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Dashboard     │
                                    │   (React App)   │
                                    └────────┬────────┘
                                             │ HTTP API calls
                                             ▼
┌──────────┐     HTTP POST      ┌─────────────────────┐
│  Client  │ ──────────────────▶│    FastAPI API      │
│  (User)  │                    │  (Job Submission)   │
└──────────┘                    └──────────┬──────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
           ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
           │  PostgreSQL   │      │   RabbitMQ    │      │     Redis     │
           │  (Metadata)   │      │   (Queues)    │      │   (Cache)     │
           └───────────────┘      └───────┬───────┘      └───────────────┘
                    ▲                     │                      ▲
                    │                     │ AMQP                 │
                    │                     ▼                      │
                    │         ┌───────────────────────┐          │
                    │         │      Workers (3x)     │          │
                    └─────────│   - Email Handler     │──────────┘
                    Updates   │   - Video Handler     │  Heartbeat
                              │   - Scraper Handler   │
                              └───────────────────────┘
                                          │
                                          │ Failed Jobs
                                          ▼
                              ┌───────────────────────┐
                              │   Dead Letter Queue   │
                              └───────────────────────┘
```

## 2.2 Component Responsibilities

| Component | Primary Responsibility | Secondary Responsibilities |
|-----------|----------------------|---------------------------|
| **API** | Accept job submissions | Query status, manage schedules |
| **Worker** | Execute jobs | Retry failed jobs, track progress |
| **Scheduler** | Trigger scheduled jobs | Calculate next run times |
| **Dashboard** | Display system state | Enable job management |
| **PostgreSQL** | Store job metadata | Persist retry history |
| **RabbitMQ** | Distribute jobs to workers | Handle priority routing |
| **Redis** | Cache real-time status | Track worker health |

## 2.3 Directory Structure

```
distributed-job-queue/
│
├── api/                          # FastAPI REST API Application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── database.py           # Database connection
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── main.py               # Application entry point
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── schemas.py            # Pydantic validation schemas
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── jobs.py           # Job CRUD endpoints
│   │       ├── stats.py          # Statistics endpoint
│   │       ├── dead_letters.py   # Dead letter management
│   │       └── scheduled_jobs.py # Scheduled job management
│   ├── alembic/                  # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── worker/                       # Background Job Processor
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── config.py             # Worker configuration
│   │   ├── database.py           # Database connection
│   │   ├── models.py             # ORM models (duplicated)
│   │   ├── consumer.py           # RabbitMQ message consumer
│   │   ├── executor.py           # Job execution engine
│   │   ├── retry_logic.py        # Exponential backoff logic
│   │   ├── main.py               # Worker entry point
│   │   └── handlers/
│   │       ├── __init__.py
│   │       ├── base.py           # Abstract handler class
│   │       ├── email_handler.py  # Email job handler
│   │       ├── video_handler.py  # Video processing handler
│   │       └── scraper_handler.py# Web scraping handler
│   ├── Dockerfile
│   └── requirements.txt
│
├── scheduler/                    # Cron-like Job Scheduler
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── config.py             # Scheduler configuration
│   │   ├── database.py           # Database connection
│   │   ├── models.py             # ScheduledJob model
│   │   └── main.py               # Scheduler entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── dashboard/                    # React Monitoring Dashboard
│   ├── public/
│   │   └── index.html            # HTML template
│   ├── src/
│   │   ├── App.js                # Main React component
│   │   ├── App.css               # Styling
│   │   ├── index.js              # React entry point
│   │   └── index.css             # Base styles
│   ├── Dockerfile
│   ├── nginx.conf                # Nginx configuration
│   └── package.json              # NPM dependencies
│
├── shared/                       # Shared Utilities
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── enums.py              # Shared enumerations
│   │   ├── rabbitmq_client.py    # RabbitMQ utility class
│   │   └── redis_client.py       # Redis utility class
│   └── setup.py                  # Package installation
│
├── scripts/
│   └── submit_test_jobs.py       # Test job submission
│
├── docker-compose.yml            # Container orchestration
├── .env.example                  # Environment variables
├── .gitignore                    # Git ignore rules
├── README.md                     # Project documentation
└── QUICKSTART.md                 # Quick start guide
```

---

# 3. Shared Components

The `shared/` directory contains utilities used by multiple services.

## 3.1 File: `shared/shared/enums.py`

**Purpose**: Defines constants and enumerations shared across all services.

```python
# Key Enumerations

class JobStatus(str, Enum):
    PENDING = "pending"      # Job created, waiting in queue
    RUNNING = "running"      # Worker is executing the job
    COMPLETED = "completed"  # Job finished successfully
    FAILED = "failed"        # Job failed after all retries
    CANCELLED = "cancelled"  # Job was cancelled by user
    RETRYING = "retrying"    # Job failed, scheduled for retry

class JobPriority(str, Enum):
    HIGH = "high"     # Processed first
    MEDIUM = "medium" # Default priority
    LOW = "low"       # Processed last

class JobType(str, Enum):
    SEND_EMAIL = "send_email"
    PROCESS_VIDEO = "process_video"
    SCRAPE_WEBSITE = "scrape_website"
```

**Why This Matters**:
- Using enums prevents typos (e.g., "pendng" vs "pending")
- Python's `str, Enum` allows direct JSON serialization
- Centralized definitions ensure consistency

**Retry Configuration**:
```python
RETRY_CONFIG = {
    JobType.SEND_EMAIL: {
        "max_retries": 3,
        "base_delay": 2,   # 2 seconds
        "max_delay": 300,  # 5 minutes cap
    },
    JobType.PROCESS_VIDEO: {
        "max_retries": 5,
        "base_delay": 5,   # 5 seconds
        "max_delay": 3600, # 1 hour cap
    },
    JobType.SCRAPE_WEBSITE: {
        "max_retries": 3,
        "base_delay": 10,  # 10 seconds
        "max_delay": 600,  # 10 minutes cap
    },
}
```

---

## 3.2 File: `shared/shared/rabbitmq_client.py`

**Purpose**: Wrapper class for RabbitMQ operations.

**Key Methods**:

| Method | Purpose | Used By |
|--------|---------|---------|
| `connect()` | Establish connection and declare queues | All services |
| `publish_job()` | Send job message to queue | API, Worker (retry) |
| `consume()` | Start consuming messages | Worker |
| `ack_message()` | Acknowledge successful processing | Worker |
| `nack_message()` | Reject message (failure) | Worker |

**How It Works**:

```python
def publish_job(self, job_id, job_type, priority, payload, delay=0):
    # 1. Determine which queue based on priority
    queue_name = QUEUE_NAMES[priority]  # e.g., "jobs.high"
    
    # 2. Create message payload
    message = {
        'job_id': job_id,
        'job_type': job_type,
        'payload': payload,
    }
    
    # 3. Set message properties (persistent, priority)
    properties = BasicProperties(
        delivery_mode=2,  # Persistent (survives restart)
        priority=10 if priority == HIGH else 5 if priority == MEDIUM else 1,
    )
    
    # 4. Publish to RabbitMQ
    self.channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=properties
    )
```

**Queue Declaration**:
```python
# Priority queues with dead letter exchange
for priority, queue_name in QUEUE_NAMES.items():
    self.channel.queue_declare(
        queue=queue_name,
        durable=True,  # Survives broker restart
        arguments={
            'x-max-priority': 10,  # Enable priority
            'x-dead-letter-exchange': 'dlx',  # Failed messages go here
        }
    )
```

---

## 3.3 File: `shared/shared/redis_client.py`

**Purpose**: Redis operations for caching and real-time data.

**Key Methods**:

| Method | Purpose | TTL |
|--------|---------|-----|
| `set_job_status()` | Cache job status | 1 hour |
| `get_job_status()` | Read cached status | - |
| `set_worker_heartbeat()` | Worker health check | 60 seconds |
| `get_active_workers()` | List alive workers | - |
| `set_json()` / `get_json()` | Store complex data | Configurable |

**Why Redis?**:
1. **Speed**: In-memory, sub-millisecond reads
2. **TTL**: Data expires automatically (heartbeats)
3. **Pub/Sub**: Real-time notifications (future use)

---

# 4. API Service

The `api/` directory contains the FastAPI REST application.

## 4.1 File: `api/app/config.py`

**Purpose**: Centralized configuration using Pydantic Settings.

```python
class Settings(BaseSettings):
    # Database connection string
    database_url: str = "postgresql://jobqueue:jobqueue123@localhost:5432/jobqueue_db"
    
    # Message broker connection
    rabbitmq_url: str = "amqp://admin:admin123@localhost:5672/"
    
    # Cache connection
    redis_url: str = "redis://localhost:6379/0"
    
    # CORS (Cross-Origin Resource Sharing)
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Job defaults
    default_max_retries: int = 3
    default_retry_base_delay: int = 2  # seconds
    
    class Config:
        env_file = ".env"  # Load from .env file
```

**How Environment Variables Work**:
1. Pydantic reads from `.env` file
2. Environment variables override `.env`
3. Docker Compose sets variables from service config
4. Code uses `settings.database_url` etc.

---

## 4.2 File: `api/app/database.py`

**Purpose**: SQLAlchemy database connection and session management.

```python
# Create database engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # Test connection before use
    pool_size=10,         # Keep 10 connections ready
    max_overflow=20,      # Allow 20 more under load
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency injection for FastAPI
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db        # Provide session to request
    finally:
        db.close()      # Always close after request
```

**Connection Pooling Explained**:
- **Why?**: Creating database connections is expensive (~50ms each)
- **How?**: Pool keeps connections open, reuses them
- **pool_size=10**: 10 connections always ready
- **max_overflow=20**: Can create 20 more if needed, then they close

---

## 4.3 File: `api/app/models.py`

**Purpose**: SQLAlchemy ORM models defining database tables.

### Job Model

```python
class Job(Base):
    __tablename__ = "jobs"
    
    # Primary key - UUID is better than auto-increment for distributed systems
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Job identification
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.MEDIUM, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    
    # Job data (JSON blob)
    payload = Column(JSON, nullable=False)
    
    # Retry tracking
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Execution info
    worker_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    retry_attempts = relationship("RetryAttempt", back_populates="job")
    dead_letter = relationship("DeadLetter", back_populates="job", uselist=False)
```

**Why UUID Instead of Auto-Increment?**:
- Distributed systems may have multiple databases
- UUIDs are globally unique without coordination
- Clients can generate IDs before submission

**Index Strategy**:
- `job_type`: Filter by type (e.g., all emails)
- `status`: Queue queries (e.g., all pending)
- `priority`: Priority ordering
- `created_at`: Time-based queries
- `scheduled_for`: Find due scheduled jobs

### RetryAttempt Model

```python
class RetryAttempt(Base):
    __tablename__ = "retry_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)  # Full stack trace
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
```

**Why Track Each Retry?**:
- **Debugging**: See exact error for each attempt
- **Analytics**: Which job types fail most?
- **Optimization**: Are retry delays appropriate?

### DeadLetter Model

```python
class DeadLetter(Base):
    __tablename__ = "dead_letters"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_id = Column(UUID, ForeignKey("jobs.id"), unique=True)  # 1:1 relationship
    job_type = Column(SQLEnum(JobType), nullable=False)
    payload = Column(JSON, nullable=False)  # Original job data
    total_attempts = Column(Integer, nullable=False)
    first_attempt_at = Column(DateTime(timezone=True), nullable=False)
    final_failure_at = Column(DateTime(timezone=True), server_default=func.now())
    failure_reason = Column(Text, nullable=False)
    all_error_messages = Column(JSON, nullable=True)  # Array of all errors
```

**Dead Letter Queue Explained**:
- Jobs that fail after all retries go here
- Original payload preserved for retry
- All error messages collected for analysis
- Can be retried manually via API

---

## 4.4 File: `api/app/schemas.py`

**Purpose**: Pydantic models for request/response validation.

### Request Schemas

```python
class JobCreateRequest(BaseModel):
    job_type: JobType                         # Required: "send_email", etc.
    priority: JobPriority = JobPriority.MEDIUM  # Optional, defaults to medium
    payload: Dict[str, Any]                   # Required: job-specific data
    max_retries: Optional[int] = 3            # Optional, defaults to 3
    scheduled_for: Optional[datetime] = None  # Optional: future execution
```

**Validation Example**:
```python
# Invalid request (missing job_type)
{"payload": {"to": "test@example.com"}}
# → 422 Unprocessable Entity: "job_type field required"

# Invalid request (wrong job_type)
{"job_type": "invalid_type", "payload": {}}
# → 422 Unprocessable Entity: "value is not a valid enumeration member"
```

### Response Schemas

```python
class JobDetailResponse(BaseModel):
    job_id: UUID
    job_type: JobType
    priority: JobPriority
    status: JobStatus
    payload: Dict[str, Any]
    max_retries: int
    retry_count: int
    created_at: datetime
    # ... more fields
    
    class Config:
        from_attributes = True  # Allow ORM model conversion
```

---

## 4.5 File: `api/app/routers/jobs.py`

**Purpose**: Job CRUD API endpoints.

### POST /api/v1/jobs - Create Job

```python
@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    job_request: JobCreateRequest,
    db: Session = Depends(get_db),             # Database session
    rabbitmq: RabbitMQClient = Depends(get_rabbitmq),  # Message queue
    redis: RedisClient = Depends(get_redis),   # Cache
):
    # 1. Create job record in database
    job = Job(
        job_type=job_request.job_type,
        priority=job_request.priority,
        payload=job_request.payload,
        max_retries=job_request.max_retries,
        scheduled_for=job_request.scheduled_for,
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)  # Get generated ID
    
    # 2. Cache job status in Redis
    redis.set_job_status(str(job.id), job.status.value)
    
    # 3. Publish to RabbitMQ (if not scheduled for future)
    if job.scheduled_for is None or job.scheduled_for <= datetime.utcnow():
        rabbitmq.publish_job(
            job_id=str(job.id),
            job_type=job.job_type.value,
            priority=job.priority,
            payload=job.payload,
        )
    
    # 4. Return response
    return JobResponse(job_id=job.id, status=job.status, created_at=job.created_at)
```

**Flow Diagram**:
```
Client Request → Validate → Save to PostgreSQL → Cache in Redis → Publish to RabbitMQ → Response
```

### GET /api/v1/jobs/{job_id} - Get Job Status

```python
@router.get("/{job_id}", response_model=JobWithRetriesResponse)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    # 1. Check Redis cache first (fast path)
    cached_status = redis.get_job_status(str(job_id))
    
    # 2. Get full details from database
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 3. Get retry history
    retry_attempts = db.query(RetryAttempt).filter(
        RetryAttempt.job_id == job_id
    ).order_by(RetryAttempt.attempt_number).all()
    
    return JobWithRetriesResponse(...)
```

---

## 4.6 File: `api/app/routers/stats.py`

**Purpose**: System statistics for dashboard.

```python
@router.get("", response_model=StatsResponse)
async def get_statistics(db: Session, redis: RedisClient):
    # Count jobs by status using SQL aggregation
    pending_jobs = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.PENDING
    ).scalar()
    
    running_jobs = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.RUNNING
    ).scalar()
    
    # etc...
    
    # Get active workers from Redis (based on heartbeats)
    active_workers = len(redis.get_active_workers())
    
    return StatsResponse(
        pending_jobs=pending_jobs,
        running_jobs=running_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        dead_letter_count=dead_letter_count,
        active_workers=active_workers,
        queue_breakdown=QueueStats(
            high=high_priority,
            medium=medium_priority,
            low=low_priority,
        ),
    )
```

---

## 4.7 File: `api/app/main.py`

**Purpose**: FastAPI application entry point.

```python
# Create FastAPI application
app = FastAPI(
    title="Distributed Job Queue API",
    description="Production-grade job queue system",
    version="1.0.0",
    docs_url="/docs",    # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# Add CORS middleware (allow dashboard to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs.router)           # /api/v1/jobs
app.include_router(stats.router)          # /api/v1/stats
app.include_router(dead_letters.router)   # /api/v1/dead-letters
app.include_router(scheduled_jobs.router) # /api/v1/scheduled-jobs

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 4.8 Alembic Database Migrations

**Purpose**: Version control for database schema.

### File: `api/alembic/versions/001_initial_schema.py`

```python
def upgrade():
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.Enum('SEND_EMAIL', 'PROCESS_VIDEO', 'SCRAPE_WEBSITE'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'RETRYING'), nullable=False),
        # ... more columns
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_job_type', 'jobs', ['job_type'])
    # ... more indexes

def downgrade():
    # Reverse all changes
    op.drop_table('jobs')
```

**Why Migrations?**:
- Track schema changes in version control
- Apply changes consistently across environments
- Roll back problematic changes
- Multiple developers can modify schema safely

---

# 5. Worker Service

The `worker/` directory contains the background job processor.

## 5.1 File: `worker/worker/retry_logic.py`

**Purpose**: Exponential backoff calculation.

```python
class RetryManager:
    
    @staticmethod
    def calculate_backoff(job_type: JobType, attempt_number: int) -> int:
        """
        Calculate delay with exponential backoff and jitter.
        
        Formula: delay = base_delay * (2 ^ attempt) + random_jitter
        
        Why jitter?
        - Without jitter: 1000 failed jobs all retry at exactly 8 seconds
        - This causes "thundering herd" - all hit the server at once
        - With jitter: Retries spread across 6.4s to 9.6s window
        """
        config = RETRY_CONFIG.get(job_type)
        base_delay = config["base_delay"]  # e.g., 2 seconds
        max_delay = config["max_delay"]    # e.g., 300 seconds
        
        # Exponential: 2, 4, 8, 16, 32, 64, 128...
        delay = base_delay * (2 ** attempt_number)
        
        # Jitter: ±20% randomization
        jitter = delay * 0.2 * (2 * random.random() - 1)
        delay_with_jitter = delay + jitter
        
        # Cap at maximum
        return min(int(delay_with_jitter), max_delay)
```

**Retry Delay Examples** (for email with base_delay=2):

| Attempt | Base Delay | With Jitter (~) | Capped At |
|---------|------------|-----------------|-----------|
| 1 | 2s | 1.6s - 2.4s | - |
| 2 | 4s | 3.2s - 4.8s | - |
| 3 | 8s | 6.4s - 9.6s | - |
| 4 | 16s | 12.8s - 19.2s | - |
| 5 | 32s | 25.6s - 38.4s | - |
| 10 | 2048s | ~1600s - 2400s | 300s (capped) |

---

## 5.2 File: `worker/worker/handlers/base.py`

**Purpose**: Abstract base class for job handlers.

```python
from abc import ABC, abstractmethod

class BaseHandler(ABC):
    """
    Abstract base class that all job handlers must inherit.
    
    This enforces a consistent interface:
    - All handlers have an execute() method
    - All handlers can validate their payload
    """
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the job. Must be implemented by subclasses.
        
        Args:
            payload: Job-specific data (e.g., email recipient, video URL)
            
        Returns:
            Result dictionary with execution details
            
        Raises:
            Exception: If job execution fails (triggers retry)
        """
        pass
    
    def validate_payload(self, payload: Dict[str, Any], required_fields: list[str]):
        """
        Validate that payload contains required fields.
        
        Args:
            payload: The job payload
            required_fields: List of field names that must exist
            
        Raises:
            ValueError: If any required field is missing
        """
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
```

---

## 5.3 File: `worker/worker/handlers/email_handler.py`

**Purpose**: Handle email sending jobs.

```python
class EmailHandler(BaseHandler):
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Validate required fields
        self.validate_payload(payload, ['to', 'subject', 'body'])
        
        to_email = payload['to']
        subject = payload['subject']
        body = payload['body']
        
        logger.info(f"Sending email to {to_email}")
        
        # 2. Simulate random failure (for testing retry logic)
        failure_rate = payload.get('failure_rate', 0.0)
        if random.random() < failure_rate:
            raise Exception(f"SMTP connection timeout to {to_email}")
        
        # 3. Simulate processing time
        time.sleep(random.uniform(0.5, 2.0))
        
        # 4. Return success result
        return {
            'status': 'sent',
            'to': to_email,
            'subject': subject,
            'sent_at': time.time(),
        }
```

**Production Note**: In a real system, this would integrate with:
- SendGrid
- AWS SES
- Mailgun
- SMTP server

---

## 5.4 File: `worker/worker/handlers/scraper_handler.py`

**Purpose**: Handle web scraping jobs.

```python
class ScraperHandler:
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = payload['url']
        selector = payload.get('selector', 'title')  # CSS selector
        timeout = payload.get('timeout', 10)
        
        try:
            # 1. Make HTTP request
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'JobQueue-Scraper/1.0'
            })
            response.raise_for_status()  # Raise on 4xx/5xx
            
            # 2. Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 3. Extract data using CSS selector
            if selector == 'title':
                data = soup.title.string if soup.title else 'No title'
            else:
                elements = soup.select(selector)
                data = [elem.get_text(strip=True) for elem in elements]
            
            return {
                'status': 'scraped',
                'url': url,
                'data': data,
                'status_code': response.status_code,
            }
            
        except requests.RequestException as e:
            raise Exception(f"Failed to scrape {url}: {e}")
```

---

## 5.5 File: `worker/worker/executor.py`

**Purpose**: Execute jobs using appropriate handlers.

```python
class JobExecutor:
    
    def __init__(self):
        # Registry of job type → handler
        self.handlers = {
            JobType.SEND_EMAIL: EmailHandler(),
            JobType.PROCESS_VIDEO: VideoHandler(),
            JobType.SCRAPE_WEBSITE: ScraperHandler(),
        }
    
    def execute(self, job_id: str, job_type: JobType, payload: dict) -> dict:
        # 1. Update job status to RUNNING
        db = get_db()
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.worker_id = settings.worker_id
        db.commit()
        db.close()
        
        # 2. Get handler for this job type
        handler = self.handlers.get(job_type)
        if not handler:
            raise ValueError(f"No handler for {job_type}")
        
        try:
            # 3. Execute the job
            result = handler.execute(payload)
            
            # 4. Update status to COMPLETED
            db = get_db()
            job = db.query(Job).filter(Job.id == job_id).first()
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            db.commit()
            db.close()
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            # 5. Capture error for retry logic
            db = get_db()
            job = db.query(Job).filter(Job.id == job_id).first()
            job.error_message = str(e)
            db.commit()
            db.close()
            
            raise  # Re-raise for consumer to handle
```

---

## 5.6 File: `worker/worker/consumer.py`

**Purpose**: Consume messages from RabbitMQ and process jobs.

```python
class JobConsumer:
    
    def on_message(self, channel, method, properties, body):
        """Called when a message arrives from RabbitMQ."""
        
        try:
            # 1. Parse message
            message = json.loads(body)
            job_id = message['job_id']
            job_type = JobType(message['job_type'])
            payload = message['payload']
            
            # 2. Execute job
            result = self.executor.execute(job_id, job_type, payload)
            
            # 3. Acknowledge success (removes from queue)
            self.rabbitmq.ack_message(method.delivery_tag)
            
        except Exception as e:
            # 4. Handle failure with retry logic
            self.handle_job_failure(job_id, job_type, payload, str(e))
            
            # 5. Acknowledge (we'll handle retry ourselves)
            self.rabbitmq.ack_message(method.delivery_tag)
    
    def handle_job_failure(self, job_id, job_type, payload, error_msg):
        """Handle failed job - retry or dead letter."""
        
        db = get_db()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        # Increment retry count
        job.retry_count += 1
        
        # Log retry attempt
        retry_attempt = RetryAttempt(
            job_id=job_id,
            attempt_number=job.retry_count,
            failed_at=datetime.utcnow(),
            error_message=error_msg,
        )
        
        if self.retry_manager.should_retry(job_type, job.retry_count, job.max_retries):
            # Calculate next retry time
            delay = self.retry_manager.calculate_backoff(job_type, job.retry_count)
            
            # Republish with delay
            job.status = JobStatus.RETRYING
            self.rabbitmq.publish_job(job_id, job_type, job.priority, payload, delay=delay)
            
        else:
            # Move to dead letter queue
            job.status = JobStatus.FAILED
            
            dead_letter = DeadLetter(
                job_id=job_id,
                job_type=job_type,
                payload=payload,
                total_attempts=job.retry_count,
                failure_reason=error_msg,
            )
            db.add(dead_letter)
        
        db.add(retry_attempt)
        db.commit()
        db.close()
```

---

## 5.7 File: `worker/worker/main.py`

**Purpose**: Worker entry point with signal handling.

```python
def main():
    # 1. Configure logging
    logging.basicConfig(level=settings.log_level)
    
    # 2. Register graceful shutdown handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Docker stop
    
    # 3. Send initial heartbeat to Redis
    redis = RedisClient(settings.redis_url)
    redis.set_worker_heartbeat(settings.worker_id, ttl=60)
    
    # 4. Start consuming jobs
    consumer = JobConsumer()
    consumer.start()  # Blocks until shutdown

def signal_handler(signum, frame):
    """Handle shutdown gracefully."""
    logger.info("Shutdown signal received")
    
    # 1. Finish current job (don't abandon it)
    # 2. Stop consuming new jobs
    # 3. Close connections
    # 4. Exit cleanly
    
    consumer.stop()
    sys.exit(0)
```

**Why Graceful Shutdown Matters**:
- Without it: Job is abandoned mid-execution → corrupted state
- With it: Current job finishes → clean exit → job not requeued

---

# 6. Scheduler Service

The `scheduler/` directory contains the cron-like job scheduler.

## 6.1 File: `scheduler/scheduler/main.py`

**Purpose**: Poll for due scheduled jobs and publish them.

```python
def main():
    logger.info("Starting scheduler")
    
    while running:
        try:
            process_scheduled_jobs()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        
        # Sleep for poll interval (default 60 seconds)
        time.sleep(settings.scheduler_poll_interval)

def process_scheduled_jobs():
    db = get_db()
    
    # 1. Find active scheduled jobs that are due
    now = datetime.utcnow()
    due_jobs = db.query(ScheduledJob).filter(
        ScheduledJob.is_active == 1,
        ScheduledJob.next_run_at <= now
    ).all()
    
    for scheduled_job in due_jobs:
        # 2. Publish job to RabbitMQ
        rabbitmq.publish_job(
            job_id=f"scheduled-{scheduled_job.id}-{int(time.time())}",
            job_type=scheduled_job.job_type.value,
            priority=scheduled_job.priority,
            payload=scheduled_job.payload,
        )
        
        # 3. Calculate next run time using croniter
        cron = croniter(scheduled_job.cron_expression, now)
        next_run = cron.get_next(datetime)
        
        # 4. Update schedule
        scheduled_job.last_run_at = now
        scheduled_job.next_run_at = next_run
        
        db.commit()
    
    db.close()
```

**Cron Expression Examples**:

| Expression | Meaning |
|------------|---------|
| `0 9 * * *` | Every day at 9:00 AM |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 * * 0` | Every Sunday at midnight |
| `0 0 1 * *` | First of every month at midnight |
| `30 4 * * 1-5` | Monday-Friday at 4:30 AM |

---

# 7. Dashboard Service

The `dashboard/` directory contains the React monitoring UI.

## 7.1 File: `dashboard/src/App.js`

**Purpose**: Main React component with dashboard UI.

```javascript
function App() {
  // State management
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [deadLetters, setDeadLetters] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch data on mount and every 5 seconds
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);  // Cleanup on unmount
  }, []);
  
  const fetchData = async () => {
    // Parallel API calls for efficiency
    const [statsRes, jobsRes, deadLettersRes] = await Promise.all([
      axios.get(`${API_URL}/api/v1/stats`),
      axios.get(`${API_URL}/api/v1/jobs?limit=20`),
      axios.get(`${API_URL}/api/v1/dead-letters?limit=10`),
    ]);
    
    setStats(statsRes.data);
    setJobs(jobsRes.data);
    setDeadLetters(deadLettersRes.data.items || []);
  };
  
  return (
    <div className="App">
      {/* Header */}
      <header>
        <h1>🚀 Distributed Job Queue Dashboard</h1>
      </header>
      
      {/* Tab Navigation */}
      <div className="tabs">
        <button onClick={() => setActiveTab('overview')}>Overview</button>
        <button onClick={() => setActiveTab('jobs')}>Jobs</button>
        <button onClick={() => setActiveTab('deadletters')}>Dead Letters</button>
      </div>
      
      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="stats-grid">
          <StatCard title="Pending Jobs" value={stats.pending_jobs} />
          <StatCard title="Running Jobs" value={stats.running_jobs} />
          <StatCard title="Completed Jobs" value={stats.completed_jobs} />
          <StatCard title="Failed Jobs" value={stats.failed_jobs} />
          <StatCard title="Active Workers" value={stats.active_workers} />
          <StatCard title="Dead Letters" value={stats.dead_letter_count} />
        </div>
      )}
      
      {/* Jobs Tab - Table of recent jobs */}
      {activeTab === 'jobs' && (
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Type</th><th>Priority</th>
              <th>Status</th><th>Retries</th><th>Created</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map(job => (
              <tr key={job.job_id}>
                <td>{job.job_id}</td>
                <td>{job.job_type}</td>
                <td><PriorityBadge priority={job.priority} /></td>
                <td><StatusBadge status={job.status} /></td>
                <td>{job.retry_count} / {job.max_retries}</td>
                <td>{formatDate(job.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      
      {/* Dead Letters Tab */}
      {activeTab === 'deadletters' && (
        // Similar table for failed jobs
      )}
    </div>
  );
}
```

**Key React Concepts Used**:
- `useState`: Manage component state
- `useEffect`: Side effects (data fetching)
- `axios`: HTTP client for API calls
- Conditional rendering with `&&`
- List rendering with `.map()`

---

## 7.2 File: `dashboard/src/App.css`

**Purpose**: Modern styling with CSS.

```css
/* Gradient background */
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

/* Card styling with shadows */
.stat-card {
  background: white;
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;  /* Smooth hover effect */
}

.stat-card:hover {
  transform: translateY(-5px);  /* Lift on hover */
}

/* Color-coded status badges */
.status-badge {
  padding: 5px 12px;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  text-transform: uppercase;
}

/* Grid layout for stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}
```

---

## 7.3 File: `dashboard/nginx.conf`

**Purpose**: Nginx configuration for serving React app and proxying API.

```nginx
server {
    listen 3000;
    
    # Serve static React files
    root /usr/share/nginx/html;
    index index.html;
    
    # SPA routing - always serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://api:8000;  # Docker service name
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

---

# 8. Infrastructure Configuration

## 8.1 File: `docker-compose.yml`

**Purpose**: Define and orchestrate all services.

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: jobqueue
      POSTGRES_PASSWORD: jobqueue123
      POSTGRES_DB: jobqueue_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jobqueue"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  # RabbitMQ Message Broker
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports:
      - "5672:5672"    # AMQP protocol
      - "15672:15672"  # Management UI
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
  
  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
  
  # FastAPI Application
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://jobqueue:jobqueue123@postgres:5432/jobqueue_db
      RABBITMQ_URL: amqp://admin:admin123@rabbitmq:5672/
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy  # Wait for DB to be ready
      rabbitmq:
        condition: service_healthy
      redis:
        condition: service_healthy
  
  # Worker Processes (3 instances)
  worker:
    build: ./worker
    deploy:
      replicas: 3  # Run 3 worker containers
    depends_on:
      - postgres
      - rabbitmq
      - redis
  
  # Job Scheduler
  scheduler:
    build: ./scheduler
    depends_on:
      - postgres
      - rabbitmq
  
  # React Dashboard
  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    depends_on:
      - api

volumes:
  postgres_data:  # Named volume for database persistence
  rabbitmq_data:
  redis_data:

networks:
  jobqueue-network:
    driver: bridge  # Private network for containers
```

**Service Dependencies**:
```
                    ┌─────────────────────┐
                    │     Dashboard       │
                    └──────────┬──────────┘
                               │ depends_on
                               ▼
                    ┌─────────────────────┐
                    │        API          │
                    └──────────┬──────────┘
                               │ depends_on
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   PostgreSQL  │      │   RabbitMQ    │      │     Redis     │
└───────────────┘      └───────────────┘      └───────────────┘
```

---

# 9. Data Flow Analysis

## 9.1 Job Submission Flow

```
1. CLIENT sends POST /api/v1/jobs
   └─→ {"job_type": "send_email", "payload": {...}}

2. API VALIDATES request with Pydantic
   └─→ Check job_type is valid enum
   └─→ Check required fields present

3. API CREATES Job record in PostgreSQL
   └─→ Status = PENDING, retry_count = 0

4. API CACHES status in Redis
   └─→ Key: "job:uuid:status" = "pending"

5. API PUBLISHES message to RabbitMQ
   └─→ Queue: "jobs.medium" (based on priority)
   └─→ Message: {"job_id": "uuid", "job_type": "send_email", ...}

6. API RETURNS response to client
   └─→ {"job_id": "uuid", "status": "pending"}
```

## 9.2 Job Processing Flow

```
1. WORKER receives message from RabbitMQ
   └─→ Consumer callback triggered

2. WORKER updates Job status to RUNNING
   └─→ PostgreSQL: status = RUNNING, started_at = now()
   └─→ Redis: update cached status

3. WORKER selects handler and executes
   └─→ EmailHandler.execute(payload)

4a. SUCCESS path:
    └─→ Update status to COMPLETED
    └─→ ACK message (removed from queue)

4b. FAILURE path:
    └─→ Log RetryAttempt
    └─→ Check retry_count < max_retries
    └─→ If yes: Calculate backoff, republish with delay
    └─→ If no: Create DeadLetter, status = FAILED
    └─→ ACK message
```

## 9.3 Monitoring Flow

```
1. DASHBOARD loads in browser
   └─→ React app mounts

2. DASHBOARD fetches /api/v1/stats every 5s
   └─→ API queries PostgreSQL for counts
   └─→ API queries Redis for active workers

3. DASHBOARD displays real-time stats
   └─→ Updates state, re-renders

4. USER clicks job row
   └─→ Fetch /api/v1/jobs/{id}
   └─→ Display details with retry history
```

---

# 10. Key Concepts Explained

## 10.1 Why RabbitMQ + PostgreSQL + Redis?

| Component | Role | Why Not Just Database? |
|-----------|------|----------------------|
| **PostgreSQL** | Persistent storage | Perfect for structured data, ACID transactions |
| **RabbitMQ** | Job distribution | Designed for message passing, built-in queuing |
| **Redis** | Real-time cache | In-memory speed, TTL for heartbeats |

**Using only PostgreSQL (naive approach)**:
```python
# Worker would poll: "SELECT * FROM jobs WHERE status = 'pending' LIMIT 1"
# Problems:
# 1. Constant polling wastes resources
# 2. Two workers might grab same job (race condition)
# 3. No priority support
# 4. Complex locking needed
```

**Using RabbitMQ (proper approach)**:
```python
# Worker subscribes and waits for messages
# Benefits:
# 1. No polling - messages pushed to workers
# 2. Each message delivered to one worker only
# 3. Built-in priority queues
# 4. Automatic requeuing on failure
```

## 10.2 Exponential Backoff Explained

**Problem**: Service is overloaded, returning errors

**Bad Solution** (constant retry):
```
Attempt 1: Fail (0s delay)
Attempt 2: Fail (0s delay)
Attempt 3: Fail (0s delay)
→ Hammering the already-overloaded service!
```

**Good Solution** (exponential backoff):
```
Attempt 1: Fail → wait 2s
Attempt 2: Fail → wait 4s
Attempt 3: Fail → wait 8s
Attempt 4: Fail → wait 16s
→ Gives service time to recover!
```

**With Jitter** (avoid synchronized retries):
```
1000 jobs all fail at the same time

Without jitter:
→ All 1000 jobs retry at exactly t+8s → another spike!

With jitter (±20%):
→ Jobs retry between t+6.4s and t+9.6s → spread load
```

## 10.3 Dead Letter Queue Explained

**Scenario**: Job keeps failing despite retries

```
Attempt 1: "Connection timeout" → retry
Attempt 2: "Connection timeout" → retry  
Attempt 3: "Connection timeout" → retry
Attempt 4: max_retries exceeded → DEAD LETTER
```

**What happens**:
1. Job moved to `dead_letters` table
2. All error messages preserved
3. Original payload saved
4. Job status set to FAILED
5. Appears in dashboard "Dead Letters" tab

**Why this matters**:
- **No job loss**: Failed jobs aren't deleted
- **Analysis**: See why jobs failed
- **Retry**: Can resubmit after fixing issue
- **Metrics**: Track failure rates

## 10.4 Priority Queue Implementation

**RabbitMQ Priority Support**:
```python
# Three separate queues
"jobs.high"   → Workers check first
"jobs.medium" → Workers check second
"jobs.low"    → Workers check last

# Message priority (0-10)
high_priority_msg.priority = 10
medium_priority_msg.priority = 5
low_priority_msg.priority = 1
```

**Worker Consumption Strategy**:
```python
# Simplified approach (our implementation)
consumer.consume("jobs.medium")  # Consume from one queue

# Production approach (round-robin with priority)
while True:
    if msg := try_consume("jobs.high"): process(msg)
    elif msg := try_consume("jobs.medium"): process(msg)
    elif msg := try_consume("jobs.low"): process(msg)
    else: wait()
```

## 10.5 Worker Scaling

**Horizontal Scaling**:
```bash
# Scale to 5 workers
docker-compose up -d --scale worker=5

# RabbitMQ distributes messages across workers
# No code changes needed!
```

**Load Distribution**:
```
Queue: [job1, job2, job3, job4, job5, job6]

Worker 1: job1, job4
Worker 2: job2, job5
Worker 3: job3, job6

→ Round-robin distribution (configurable)
```

---

## Summary

This distributed job queue system demonstrates:

1. **Clean Architecture**: Separation of concerns (API, Worker, Scheduler, Dashboard)
2. **Production Patterns**: Retry logic, dead letters, priority queues
3. **Scalability**: Horizontal worker scaling, connection pooling
4. **Observability**: Real-time monitoring, comprehensive logging
5. **Reliability**: Graceful shutdown, message persistence
6. **Modern Stack**: FastAPI, React, Docker, PostgreSQL, RabbitMQ, Redis

Each component has a single responsibility and communicates through well-defined interfaces (REST API, AMQP messages, database records).

---

**This documentation serves as both a learning resource and technical reference for the project.**
