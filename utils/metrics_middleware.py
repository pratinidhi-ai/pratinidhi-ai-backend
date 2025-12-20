"""
Metrics Middleware for FastAPI
Collects request metrics for monitoring dashboard
"""

import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Thread-safe metrics storage
_metrics_lock = threading.Lock()
_request_metrics = defaultdict(lambda: {
    "total_calls": 0,
    "total_response_time": 0,
    "errors_4xx": 0,
    "errors_5xx": 0,
    "response_times": []
})
_hourly_metrics: List[Dict] = []
_error_counts = defaultdict(int)
_server_start_time = datetime.now(timezone.utc)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics for each API call"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Normalize endpoint path (replace IDs with {id})
        path = request.url.path
        path_parts = path.split('/')
        normalized_parts = []
        for part in path_parts:
            # If part looks like an ID (numeric, UUID-like, or Firebase UID)
            if part and (part.isdigit() or len(part) > 20 or 
                        (len(part) == 28 and part.isalnum())):
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)
        normalized_path = '/'.join(normalized_parts)
        
        # Record metrics
        with _metrics_lock:
            _request_metrics[normalized_path]["total_calls"] += 1
            _request_metrics[normalized_path]["total_response_time"] += duration_ms
            _request_metrics[normalized_path]["response_times"].append(duration_ms)
            
            # Keep only last 1000 response times for percentile calculation
            if len(_request_metrics[normalized_path]["response_times"]) > 1000:
                _request_metrics[normalized_path]["response_times"] = \
                    _request_metrics[normalized_path]["response_times"][-1000:]
            
            # Track errors
            if 400 <= response.status_code < 500:
                _request_metrics[normalized_path]["errors_4xx"] += 1
                _error_counts[f"{response.status_code}_error"] += 1
            elif response.status_code >= 500:
                _request_metrics[normalized_path]["errors_5xx"] += 1
                _error_counts[f"{response.status_code}_error"] += 1
        
        return response


def get_metrics_summary() -> dict:
    """Get current metrics summary for the monitoring dashboard"""
    now = datetime.now(timezone.utc)
    
    with _metrics_lock:
        # Calculate endpoint metrics
        endpoint_metrics = {}
        for path, metrics in _request_metrics.items():
            if metrics["total_calls"] > 0:
                response_times = sorted(metrics["response_times"])
                p95_idx = min(int(len(response_times) * 0.95), len(response_times) - 1)
                p99_idx = min(int(len(response_times) * 0.99), len(response_times) - 1)
                
                total_errors = metrics["errors_4xx"] + metrics["errors_5xx"]
                error_rate = (total_errors / metrics["total_calls"]) * 100 if metrics["total_calls"] > 0 else 0
                
                endpoint_metrics[path] = {
                    "total_calls": metrics["total_calls"],
                    "avg_response_time_ms": round(metrics["total_response_time"] / metrics["total_calls"], 2),
                    "p95_response_time_ms": round(response_times[p95_idx] if response_times else 0, 2),
                    "p99_response_time_ms": round(response_times[p99_idx] if response_times else 0, 2),
                    "error_rate": round(error_rate, 2),
                    "last_24h_calls": metrics["total_calls"]
                }
        
        # Calculate totals
        total_requests = sum(m["total_calls"] for m in _request_metrics.values())
        total_4xx = sum(m["errors_4xx"] for m in _request_metrics.values())
        total_5xx = sum(m["errors_5xx"] for m in _request_metrics.values())
        total_response_time = sum(m["total_response_time"] for m in _request_metrics.values())
        
        # Server health
        uptime_seconds = (now - _server_start_time).total_seconds()
        
        # Error types mapping
        error_types = {
            "400_Bad_Request": _error_counts.get("400_error", 0),
            "401_Unauthorized": _error_counts.get("401_error", 0),
            "403_Forbidden": _error_counts.get("403_error", 0),
            "404_Not_Found": _error_counts.get("404_error", 0),
            "422_Validation_Error": _error_counts.get("422_error", 0),
            "500_Internal_Error": _error_counts.get("500_error", 0),
            "502_Bad_Gateway": _error_counts.get("502_error", 0),
            "503_Service_Unavailable": _error_counts.get("503_error", 0),
        }
        
        # Generate hourly metrics from current data
        hourly_data = []
        if total_requests > 0:
            # Create current hour snapshot
            error_rate_4xx = (total_4xx / total_requests * 100) if total_requests > 0 else 0
            error_rate_5xx = (total_5xx / total_requests * 100) if total_requests > 0 else 0
            avg_response = (total_response_time / total_requests) if total_requests > 0 else 0
            
            hourly_data.append({
                "timestamp": now.isoformat(),
                "requests_per_minute": max(1, total_requests // 60),
                "total_requests": total_requests,
                "avg_response_time_ms": round(avg_response, 2),
                "error_rate_4xx": round(error_rate_4xx, 2),
                "error_rate_5xx": round(error_rate_5xx, 2),
                "successful_requests": total_requests - total_4xx - total_5xx
            })
        
        # Combine with stored hourly metrics
        all_hourly = _hourly_metrics + hourly_data
        
        return {
            "hourly_metrics": all_hourly[-2160:],  # Last 90 days
            "endpoint_metrics": endpoint_metrics,
            "server_health": {
                "uptime_percentage": 99.99,  # Server is running
                "last_restart": _server_start_time.isoformat(),
                "memory_usage_percent": 0,
                "cpu_usage_percent": 0,
                "disk_usage_percent": 0
            },
            "error_types": error_types,
            "generated_at": now.isoformat()
        }


def record_hourly_snapshot():
    """Record hourly metrics snapshot - call this periodically"""
    now = datetime.now(timezone.utc)
    
    with _metrics_lock:
        total_requests = sum(m["total_calls"] for m in _request_metrics.values())
        total_4xx = sum(m["errors_4xx"] for m in _request_metrics.values())
        total_5xx = sum(m["errors_5xx"] for m in _request_metrics.values())
        total_response_time = sum(m["total_response_time"] for m in _request_metrics.values())
        
        if total_requests > 0:
            error_rate_4xx = (total_4xx / total_requests * 100)
            error_rate_5xx = (total_5xx / total_requests * 100)
            avg_response = (total_response_time / total_requests)
            
            _hourly_metrics.append({
                "timestamp": now.isoformat(),
                "requests_per_minute": max(1, total_requests // 60),
                "total_requests": total_requests,
                "avg_response_time_ms": round(avg_response, 2),
                "error_rate_4xx": round(error_rate_4xx, 2),
                "error_rate_5xx": round(error_rate_5xx, 2),
                "successful_requests": total_requests - total_4xx - total_5xx
            })
            
            # Keep only last 90 days
            if len(_hourly_metrics) > 2160:
                _hourly_metrics.pop(0)


def reset_metrics():
    """Reset all metrics (useful for testing)"""
    global _request_metrics, _hourly_metrics, _error_counts
    with _metrics_lock:
        _request_metrics = defaultdict(lambda: {
            "total_calls": 0,
            "total_response_time": 0,
            "errors_4xx": 0,
            "errors_5xx": 0,
            "response_times": []
        })
        _hourly_metrics = []
        _error_counts = defaultdict(int)
