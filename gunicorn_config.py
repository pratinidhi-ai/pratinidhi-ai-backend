import os
import multiprocessing

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "uvicorn.workers.UvicornWorker"  # Required for FastAPI
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pratinidhi-ai-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for better performance
preload_app = True

# Restart workers after this many requests (helps with memory leaks)
max_requests = 1000
max_requests_jitter = 50


def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Gunicorn server starting...")


def on_reload(server):
    """Called when configuration is reloaded."""
    server.log.info("Gunicorn configuration reloaded")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn server is ready to handle requests")


def worker_int(worker):
    """Called when worker receives INT or QUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")


def worker_abort(worker):
    """Called when worker receives SIGABRT signal."""
    worker.log.warning("Worker received SIGABRT signal")
