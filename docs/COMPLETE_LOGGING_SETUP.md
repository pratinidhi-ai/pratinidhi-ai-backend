# Complete Logging Setup for AWS App Runner

## Problem Solved
Your application was using `logging.getLogger()` in various modules but **never configured the root logger**, so no logs were being output to stdout where AWS App Runner collects them.

## Changes Made

### 1. **app.py** - Root Logger Configuration
Added comprehensive logging setup that:
- Configures the root logger with `logging.basicConfig()`
- Sends all logs to `stdout` (required for AWS App Runner)
- Uses environment variable `LOG_LEVEL` for easy configuration
- Formats logs with timestamps, module names, and log levels
- Uses `force=True` to override any existing configuration

```python
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
```

### 2. **gunicorn_config.py** - Gunicorn Logging
Created Gunicorn configuration that:
- Sends access logs to stdout (`-`)
- Sends error logs to stderr (`-`)
- Respects `LOG_LEVEL` environment variable
- Includes detailed access log format with request timing
- Configures workers and timeout settings

### 3. **Dockerfile** - Updated CMD
Changed from inline parameters to config file:
```dockerfile
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
```

## Log Levels

You can control logging verbosity with the `LOG_LEVEL` environment variable:

| Level | What You'll See |
|-------|----------------|
| `DEBUG` | Everything - all debug, info, warning, error, critical |
| `INFO` | Info and above - normal operations, warnings, errors |
| `WARNING` | Only warnings, errors, and critical |
| `ERROR` | Only errors and critical issues |
| `CRITICAL` | Only critical failures |

**Recommended:**
- Development: `DEBUG` or `INFO`
- Production: `INFO` or `WARNING`

## Setting LOG_LEVEL in AWS App Runner

### Method 1: AWS Console
1. Go to AWS App Runner Console
2. Select your service
3. Click "Configuration" tab
4. Click "Edit" under "Environment variables"
5. Add: `LOG_LEVEL` = `INFO` (or your preferred level)
6. Save and deploy

### Method 2: AWS CLI
```bash
aws apprunner update-service \
  --service-arn "your-service-arn" \
  --source-configuration "{
    \"CodeRepository\": {
      \"SourceCodeVersion\": {
        \"Type\": \"BRANCH\",
        \"Value\": \"main\"
      }
    }
  }" \
  --instance-configuration "{
    \"EnvironmentVariables\": [
      {
        \"Name\": \"LOG_LEVEL\",
        \"Value\": \"INFO\"
      }
    ]
  }"
```

## Deployment Steps

1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Add comprehensive logging configuration"
   git push
   ```

2. **Build and push to ECR:**
   ```powershell
   .\deploy-aws.ps1
   ```

3. **Deploy to App Runner:**
   - If using auto-deploy from ECR, it will update automatically
   - Otherwise, trigger manual deployment in App Runner console

## What You'll See in CloudWatch Logs

After deployment, you'll see comprehensive logs including:

### Application Startup
```
2025-11-10 10:00:00 - __main__ - INFO - Application starting with log level: INFO
2025-11-10 10:00:00 - __main__ - INFO - Flask app initialized
2025-11-10 10:00:01 - gunicorn.error - INFO - Gunicorn server is ready to handle requests
```

### HTTP Requests (from Gunicorn)
```
172.31.10.5 - - [10/Nov/2025:10:01:23] "GET / HTTP/1.1" 200 45 "-" "ELB-HealthChecker/2.0" 1234
```

### Your Application Logs
```
2025-11-10 10:01:30 - __main__ - INFO - Health check endpoint called
2025-11-10 10:01:35 - routes.tutor_routing - INFO - Step 1: Getting session abc-123
2025-11-10 10:01:36 - routes.tutor_routing - INFO - Step 2: Calling OpenAI API
2025-11-10 10:01:38 - routes.tutor_routing - INFO - OpenAI API call successful, response length: 1234
```

### Errors (with stack traces)
```
2025-11-10 10:02:15 - routes.tutor_routing - ERROR - Error creating session: Connection timeout
Traceback (most recent call last):
  File "routes/tutor_routing.py", line 45, in create_session
    ...
```

## Viewing Logs

### AWS Console (Easiest)
1. AWS App Runner → Your Service → "Logs" tab
2. View real-time logs or filter by time range

### CloudWatch Logs
1. CloudWatch Console → Logs → Log groups
2. Find: `/aws/apprunner/<service-name>/<service-id>/application`
3. Use CloudWatch Insights for advanced queries

### AWS CLI
```powershell
# Get your service details
aws apprunner describe-service --service-arn <your-service-arn>

# Tail logs in real-time
aws logs tail /aws/apprunner/<service-name>/<service-id>/application --follow --region us-east-1

# Filter for errors only
aws logs tail /aws/apprunner/<service-name>/<service-id>/application --filter-pattern "ERROR" --follow

# Search last hour
aws logs filter-log-events \
  --log-group-name /aws/apprunner/<service-name>/<service-id>/application \
  --start-time $(($(date +%s) - 3600))000 \
  --filter-pattern "ERROR"
```

## Advanced CloudWatch Queries

Use CloudWatch Insights for powerful queries:

```sql
# Count errors by module
fields @timestamp, @message
| filter @message like /ERROR/
| parse @message /(?<timestamp>.*) - (?<module>.*) - (?<level>.*) - (?<message>.*)/
| stats count() by module
| sort count desc

# Find slow requests (>1000ms)
fields @timestamp, @message
| filter @message like /GET|POST/
| parse @message /.*"(?<method>.*) (?<path>.*) HTTP.*" (?<status>\d+) (?<size>\d+) .* (?<time>\d+)$/
| filter time > 1000
| sort time desc

# Track tutor session errors
fields @timestamp, @message
| filter @message like /tutor_routing/
| filter @message like /ERROR/
```

## Troubleshooting

### Still not seeing logs?

1. **Check log level:**
   - Ensure `LOG_LEVEL` environment variable is set to `INFO` or `DEBUG`
   
2. **Verify stdout:**
   - Logs must go to stdout/stderr for App Runner to collect them
   - Check `logging.StreamHandler(sys.stdout)` is in place

3. **Gunicorn config:**
   - Ensure `accesslog = "-"` and `errorlog = "-"` in gunicorn_config.py
   
4. **Check CloudWatch log group:**
   - Verify log group exists: `/aws/apprunner/<service-name>/<service-id>/application`
   - Check IAM permissions for App Runner to write to CloudWatch

5. **Force new deployment:**
   ```bash
   aws apprunner start-deployment --service-arn <your-service-arn>
   ```

### Too many logs?

Change `LOG_LEVEL` to `WARNING` to see only warnings and errors.

### Need structured logging?

Consider adding JSON formatting:
```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'module': record.name,
            'message': record.getMessage(),
            'path': record.pathname,
            'line': record.lineno
        })

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(handlers=[handler], level=logging.INFO)
```

## Testing Locally

Test logging before deploying:

```powershell
# Build Docker image
docker build -t pratinidhi-backend .

# Run with DEBUG logging
docker run -p 8080:8080 -e LOG_LEVEL=DEBUG pratinidhi-backend

# Run with INFO logging (production-like)
docker run -p 8080:8080 -e LOG_LEVEL=INFO pratinidhi-backend

# Make a request and watch logs
curl http://localhost:8080/
```

## Summary

✅ Root logger configured in `app.py`
✅ All logs go to stdout (AWS App Runner compatible)
✅ Gunicorn access and error logs enabled
✅ Environment variable control with `LOG_LEVEL`
✅ Detailed log format with timestamps and module names
✅ Error handlers log to CloudWatch
✅ All existing logger statements now work

**Next Steps:**
1. Deploy the changes
2. Set `LOG_LEVEL=INFO` in App Runner environment variables
3. Check CloudWatch Logs - you should now see complete logs!
