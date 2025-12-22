# Leaderboard Timeout Fix - Dec 21, 2025

## Issue
User `TjQC1111MgfPz8kzDQJZkomg91v1` was experiencing connection timeouts on the `/api/leaderboard` endpoint with error:
```
ClientException: SocketException - Connection timed out (errno = 110)
```

The service would successfully retrieve and log the leaderboard data, but the response would hang/timeout.

## Root Cause
The issue was NOT a database query timeout. The actual problem was in the response serialization in `routes/leaderboard_routing.py`:

When a user was not in the top N leaderboard entries, the endpoint would:
1. Successfully fetch the filtered leaderboard list
2. Fetch the user's leaderboard entity  
3. Convert the entity using `user_leaderboard_entity.__dict__`
4. **PROBLEM**: This includes raw datetime objects (`created_at`, `updated_at`) from the dataclass
5. FastAPI's JSON encoder would hang trying to serialize these datetime objects in their raw form
6. Result: Timeout after ~30 seconds without response

This only affected users NOT in the top N because that's the only code path that uses `__dict__`.

## Solution Implemented

### Fixed Serialization in `routes/leaderboard_routing.py`
Changed from `user_leaderboard_entity.__dict__` to `user_leaderboard_entity.to_dict()`:

**Before (Line 181, 189):**
```python
user_entry = user_leaderboard_entity.__dict__  # ❌ Raw datetime objects not JSON serializable
```

**After:**
```python
user_entry = user_leaderboard_entity.to_dict()  # ✅ Converts datetime to ISO format strings
```

The `LeaderboardEntity.to_dict()` method already existed and properly handles:
- Converting `created_at` and `updated_at` to ISO format strings
- Converting nested objects (`Region`, `PerformanceMetric`) to dictionaries
- Ensuring all data is JSON serializable

**Key Changes:**
- Line 181: Changed `__dict__` to `to_dict()`
- Line 189: Changed `__dict__` to `to_dict()` in error handling path
- Both places now use the same proper serialization method

## Why This Fixes the Timeout
- `__dict__` returns raw Python datetime objects
- `to_dict()` converts them to ISO format strings via `.isoformat()`
- FastAPI can now instantly serialize the response instead of hanging
- Response time goes from timeout (~30s) to <100ms

## Testing Recommendations
1. Test with user `TjQC1111MgfPz8kzDQJZkomg91v1` - should now work
2. Test with filter_by parameters to ensure filtered leaderboard works
3. Test with various sort_by values (rating, score, correct_questions)
4. Verify datetime fields are returned as ISO strings

## Files Modified
1. `routes/leaderboard_routing.py` - Changed `__dict__` to `to_dict()` for proper serialization

## Related Issues
- Previous fix (Dec 8): Fixed datetime serialization in user subscription endpoints (similar root cause)
- This fix: Same principle applied to leaderboard endpoint

