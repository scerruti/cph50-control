# ChargePoint Data Access Layer (DAL)

A caching, rate-limited Python library for accessing ChargePoint API data. Designed for use by both classification and reporting tools.

## Features
- Transparent local caching of session/activity data
- Strict, configurable rate limiting (token bucket)
- Simple interface for batch session retrieval
- Thread-safe
- Pluggable for future backend support (python-chargepoint, direct API)

## Usage Example
```python
from chargepoint_dal import ChargePointDAL

dal = ChargePointDAL(
    username="your@email.com",
    password="yourpassword",
    cache_path="/tmp/chargepoint_cache.json",
    rate_limit=6,  # max 6 requests
    rate_period=60.0  # per 60 seconds
)

sessions = dal.get_sessions(max_batches=10, batch_size=10)
for session in sessions:
    print(session)
```

## Rate Limiting
- Default: 6 requests per minute (configurable)
- Uses a token bucket algorithm
- Prevents API bans and respects ChargePoint's limits

## Caching
- All session fetches are cached by parameters
- Cache is stored as a JSON file if `cache_path` is provided
- Thread-safe for concurrent access

## Extending
- Add methods for session details, status, etc. as needed
- Backend can be swapped for direct API or other libraries

## Requirements
- `python-chargepoint` (install via pip)

## License
MIT
