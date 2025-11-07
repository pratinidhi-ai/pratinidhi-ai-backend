# Logger vs Print: Advantages and Use Cases

## Quick Answer
**For debugging during development:** Use `print()` - it's immediate and visible.
**For production applications:** Use `logger` - it's professional, configurable, and powerful.

## Advantages of Logger over Print

### 1. **Log Levels** (Most Important)
```python
logger.debug("Detailed diagnostic info")      # Only in debug mode
logger.info("General information")            # Normal operation
logger.warning("Something unexpected")        # Potential issues
logger.error("Error occurred")                # Errors
logger.critical("Critical failure")           # System failure
```

**Benefit:** You can control what gets logged based on environment:
- Development: Show DEBUG and above
- Production: Show only WARNING and above
- Testing: Show INFO and above

**With print():** Everything always prints, cluttering production logs.

### 2. **Configurable Output**
```python
# Configure logger to:
# - Write to file
# - Send to monitoring service (CloudWatch, Datadog)
# - Format with timestamps, module names, line numbers
# - Separate error logs from info logs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
```

**Output example:**
```
2025-11-06 14:23:45,123 - math_ai_video_generator - INFO - Connecting to Knolify
2025-11-06 14:23:46,456 - math_ai_video_generator - ERROR - Connection failed
```

**With print():** Always goes to stdout, no timestamps, no context.

### 3. **Context Information**
Logger automatically adds:
- Timestamp
- Module name
- Function name
- Line number
- Thread ID
- Log level

**With print():** You have to manually add all this info.

### 4. **Production-Ready**
```python
# Logger can be configured to:
# - Rotate log files (keep last 7 days)
# - Compress old logs
# - Send errors to Slack/Email
# - Filter sensitive data
# - Aggregate logs across multiple servers

from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=5)
logger.addHandler(handler)
```

**With print():** No log management, no monitoring, no alerting.

### 5. **Performance in Production**
```python
# Logger can be disabled for performance
logger.setLevel(logging.WARNING)  # Ignore debug/info logs

# With print(), you'd need to comment out or delete code
# print("Debug info")  # Commented out in production
```

### 6. **Professional Standards**
- Logger is the industry standard for Python applications
- Expected in production code
- Required for debugging production issues
- Works with monitoring tools

### 7. **Filtering and Searching**
```python
# Different loggers for different modules
video_logger = logging.getLogger('video_generator')
api_logger = logging.getLogger('api')

# Can filter logs by module in production
# Show only video_generator logs
logging.getLogger('video_generator').setLevel(logging.DEBUG)
logging.getLogger('api').setLevel(logging.WARNING)
```

**With print():** All output mixed together, hard to filter.

## When to Use Each

### Use `print()` for:
✅ Quick debugging during development
✅ Interactive scripts/tools
✅ Simple one-off scripts
✅ When you need immediate visible output
✅ Teaching/learning code examples
✅ Command-line tools with user output

### Use `logger` for:
✅ Production applications
✅ APIs and web services
✅ Long-running services
✅ Code that will be deployed
✅ When you need log rotation
✅ When you need to monitor errors
✅ Team projects with multiple developers
✅ When debugging production issues

## Real Example: Why Logger Matters

### Scenario: Production Bug
**With print():**
```python
print("Processing request")
print("Video generation started")
print("Error: Connection timeout")  # Where? When? Which request?
```

When you get a bug report: "Video failed at 2 AM"
- No timestamp to correlate
- No way to know which request
- No way to filter by severity
- No automatic alerting

**With logger:**
```python
logger.info("Processing request for user_id=123", extra={'request_id': 'abc-123'})
logger.info("Video generation started", extra={'video_id': 'vid-456'})
logger.error("Connection timeout", exc_info=True, extra={'attempt': 3})
```

Output in production:
```
2025-11-06 02:15:23 - INFO - Processing request for user_id=123 [request_id=abc-123]
2025-11-06 02:15:24 - INFO - Video generation started [video_id=vid-456]
2025-11-06 02:15:54 - ERROR - Connection timeout [attempt=3]
Traceback (most recent call last):
  File "video_generator.py", line 45, in _send_request
    await websocket.recv()
TimeoutError: Connection timeout after 30 seconds
```

Now you can:
- Search logs by timestamp
- Filter by error level
- Get automatic alerts for ERROR level
- See full stack trace
- Correlate with other requests

## Hybrid Approach (What We Did)

During development, we changed to `print()` because:
1. **Immediate visibility** - You can see what's happening right away
2. **No configuration needed** - Works out of the box
3. **Debugging the stuck loop** - Need to see exact responses

For production, you should:
1. **Change back to logger** - Better for deployed apps
2. **Configure log level** - Control verbosity
3. **Set up log aggregation** - CloudWatch, Datadog, etc.
4. **Add monitoring** - Alert on errors

## Code to Switch Back to Logger

In your `.env` or environment:
```bash
LOG_LEVEL=INFO  # or DEBUG for development
```

In code:
```python
import os
import logging

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Now logger.info() will only show if LOG_LEVEL=INFO or DEBUG
# But logger.error() will always show
```

## Summary

| Feature | print() | logger |
|---------|---------|--------|
| Speed to use | ⚡ Instant | 🔧 Needs setup |
| Development | ✅ Great | ✅ Great |
| Production | ❌ Poor | ✅ Excellent |
| Timestamps | ❌ Manual | ✅ Automatic |
| Log levels | ❌ No | ✅ Yes |
| File output | ❌ Need redirect | ✅ Built-in |
| Monitoring | ❌ No | ✅ Yes |
| Filtering | ❌ Hard | ✅ Easy |
| Performance | ✅ Fast | ✅ Configurable |

**Best practice:** Use `print()` for quick debugging, use `logger` for everything else.
