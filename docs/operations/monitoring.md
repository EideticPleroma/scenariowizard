# Monitoring and Observability (MVP)

This document describes the simplified monitoring and observability strategy for the QA Scenario Writer MVP system.

## Overview

The MVP monitoring system provides basic visibility into system health and performance through simple logging and health checks. Advanced monitoring features are deferred to post-MVP phases.

## Monitoring Stack (Simplified)

### Basic Monitoring (MVP)
- **Application Logs**: Structured logging with basic metrics
- **Health Checks**: Service availability monitoring
- **Error Tracking**: Exception handling and reporting
- **Basic Metrics**: Request count, response time, success rate

### Post-MVP Monitoring (Future)
- **Prometheus**: Time-series metrics collection
- **Grafana**: Metrics visualization and dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Log aggregation and analysis

## Key Metrics (MVP)

### Application Metrics

#### Request Metrics
```python
# Basic HTTP Request Metrics
http_requests_total{method, endpoint, status_code}
http_request_duration_seconds{method, endpoint}
http_requests_in_flight{method, endpoint}

# API Endpoint Metrics
api_requests_total{endpoint, method, status_code}
api_request_duration_seconds{endpoint, method}
api_response_size_bytes{endpoint, method}
```

#### Business Metrics
```python
# Document Processing Metrics
documents_uploaded_total
documents_processed_total{status}
documents_processing_duration_seconds

# Scenario Generation Metrics
scenarios_generated_total{test_type, provider}
scenario_generation_duration_seconds{test_type, provider}
scenario_generation_success_rate{provider}

# MCP Tool Metrics
mcp_tool_executions_total{tool_name, status}
mcp_tool_duration_seconds{tool_name}
mcp_tool_success_rate{tool_name}
```

#### System Metrics
```python
# Database Metrics
database_connections_active
database_query_duration_seconds{query_type}
database_errors_total{error_type}

# LLM Provider Metrics
llm_requests_total{provider, status}
llm_request_duration_seconds{provider}
llm_tokens_used_total{provider}
llm_errors_total{provider, error_type}

# File Storage Metrics
files_uploaded_total
files_processed_total
file_storage_usage_bytes
```

## Logging Strategy

### Structured Logging
```python
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened
- **ERROR**: An error occurred but the application can continue
- **CRITICAL**: A serious error occurred

### Log Format
```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "level": "INFO",
  "logger": "qa_scenario_writer",
  "message": "Document uploaded successfully",
  "document_id": "doc_1234567890",
  "filename": "user_stories.md",
  "file_size": 1024,
  "user_id": "user_123",
  "request_id": "req_abc123"
}
```

## Health Checks

### Application Health Check
```python
@app.get("/health")
async def health_check():
    """Check application health status"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await check_database_health(),
            "llm_providers": await check_llm_health(),
            "file_storage": await check_file_storage_health()
        }
    }
    
    # Determine overall health
    all_healthy = all(
        service["status"] == "healthy" 
        for service in health_status["services"].values()
    )
    
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    
    return health_status
```

### Database Health Check
```python
async def check_database_health():
    """Check database connectivity and performance"""
    try:
        # Test database connection
        start_time = time.time()
        await db.execute("SELECT 1")
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "connection_pool": {
                "active": db.pool.size(),
                "idle": db.pool.idle()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### LLM Provider Health Check
```python
async def check_llm_health():
    """Check LLM provider availability"""
    health_status = {}
    
    for provider_name, provider in llm_service.providers.items():
        try:
            is_healthy = await provider.health_check()
            health_status[provider_name] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            health_status[provider_name] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    return health_status
```

## Error Tracking

### Exception Handling
```python
import traceback
from typing import Dict, Any

class ErrorTracker:
    def __init__(self):
        self.error_counts = {}
        self.error_details = []
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track error occurrence and context"""
        error_type = type(error).__name__
        
        # Increment error count
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Store error details
        error_detail = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.error_details.append(error_detail)
        
        # Log error
        logger.error(
            "Error occurred",
            error_type=error_type,
            error_message=str(error),
            context=context
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for health check"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts,
            "recent_errors": self.error_details[-10:]  # Last 10 errors
        }
```

### Error Response Format
```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "2025-01-27T10:30:00Z",
  "request_id": "req_abc123"
}
```

## Basic Metrics Collection

### Request Metrics
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

REQUESTS_IN_FLIGHT = Gauge(
    'http_requests_in_flight',
    'HTTP requests currently in flight',
    ['method', 'endpoint']
)

# Business metrics
DOCUMENTS_UPLOADED = Counter(
    'documents_uploaded_total',
    'Total documents uploaded'
)

SCENARIOS_GENERATED = Counter(
    'scenarios_generated_total',
    'Total scenarios generated',
    ['test_type', 'provider']
)

# System metrics
DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections'
)

LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'status']
)
```

### Metrics Middleware
```python
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect request metrics"""
    start_time = time.time()
    
    # Increment requests in flight
    REQUESTS_IN_FLIGHT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    try:
        response = await call_next(request)
        
        # Record request metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        return response
        
    finally:
        # Decrement requests in flight
        REQUESTS_IN_FLIGHT.labels(
            method=request.method,
            endpoint=request.url.path
        ).dec()
```

## Alerting (Basic)

### Health Check Alerts
```python
class HealthAlertManager:
    def __init__(self):
        self.alert_thresholds = {
            "response_time_ms": 5000,  # 5 seconds
            "error_rate": 0.05,  # 5%
            "memory_usage": 0.8,  # 80%
            "disk_usage": 0.9  # 90%
        }
    
    async def check_alerts(self, health_status: Dict[str, Any]):
        """Check for alert conditions"""
        alerts = []
        
        # Check response time
        if health_status.get("response_time_ms", 0) > self.alert_thresholds["response_time_ms"]:
            alerts.append({
                "type": "high_response_time",
                "message": f"Response time {health_status['response_time_ms']}ms exceeds threshold",
                "severity": "warning"
            })
        
        # Check error rate
        error_rate = health_status.get("error_rate", 0)
        if error_rate > self.alert_thresholds["error_rate"]:
            alerts.append({
                "type": "high_error_rate",
                "message": f"Error rate {error_rate:.2%} exceeds threshold",
                "severity": "critical"
            })
        
        return alerts
```

### Log-based Alerts
```python
# Simple log-based alerting
def check_log_alerts():
    """Check for alert conditions in logs"""
    alerts = []
    
    # Check for critical errors
    critical_errors = get_recent_errors(level="CRITICAL", minutes=5)
    if len(critical_errors) > 0:
        alerts.append({
            "type": "critical_errors",
            "message": f"{len(critical_errors)} critical errors in last 5 minutes",
            "severity": "critical"
        })
    
    # Check for LLM failures
    llm_failures = get_llm_failures(minutes=10)
    if len(llm_failures) > 5:
        alerts.append({
            "type": "llm_failures",
            "message": f"{len(llm_failures)} LLM failures in last 10 minutes",
            "severity": "warning"
        })
    
    return alerts
```

## Monitoring Dashboard (Basic)

### Health Status Dashboard
```python
@app.get("/monitoring/health")
async def health_dashboard():
    """Basic health monitoring dashboard"""
    health_status = await health_check()
    error_summary = error_tracker.get_error_summary()
    alerts = await alert_manager.check_alerts(health_status)
    
    return {
        "overall_status": health_status["status"],
        "services": health_status["services"],
        "errors": error_summary,
        "alerts": alerts,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Metrics Dashboard
```python
@app.get("/monitoring/metrics")
async def metrics_dashboard():
    """Basic metrics dashboard"""
    return {
        "requests": {
            "total": REQUEST_COUNT._value.sum(),
            "in_flight": REQUESTS_IN_FLIGHT._value.sum()
        },
        "documents": {
            "uploaded": DOCUMENTS_UPLOADED._value.sum(),
            "processed": get_processed_documents_count()
        },
        "scenarios": {
            "generated": SCENARIOS_GENERATED._value.sum(),
            "by_type": get_scenarios_by_type()
        },
        "llm": {
            "requests": LLM_REQUESTS._value.sum(),
            "by_provider": get_llm_requests_by_provider()
        }
    }
```

## Troubleshooting

### Common Issues

1. **High Response Time**
   - Check database connection pool
   - Verify LLM provider response times
   - Check for long-running queries

2. **High Error Rate**
   - Check application logs for error patterns
   - Verify LLM API keys and quotas
   - Check database connectivity

3. **Memory Issues**
   - Check for memory leaks in long-running processes
   - Verify file upload size limits
   - Check database connection pool size

4. **LLM Provider Issues**
   - Verify API keys and quotas
   - Check network connectivity
   - Test fallback providers

### Debugging Commands

```bash
# Check application health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/monitoring/metrics

# Check logs
docker logs qa-scenario-writer

# Check MCP server health
curl http://localhost:8001/health
```

## Post-MVP Enhancements

### Advanced Monitoring (Future)
- **Prometheus Integration**: Full metrics collection
- **Grafana Dashboards**: Rich visualization
- **Jaeger Tracing**: Distributed request tracing
- **ELK Stack**: Log aggregation and analysis
- **AlertManager**: Advanced alerting rules
- **PagerDuty**: Incident management

### Performance Monitoring
- **APM Integration**: Application performance monitoring
- **Database Monitoring**: Query performance analysis
- **LLM Monitoring**: Token usage and cost tracking
- **User Experience**: Real user monitoring

This simplified monitoring approach provides essential visibility for the MVP while maintaining the flexibility to add advanced monitoring features in future phases.