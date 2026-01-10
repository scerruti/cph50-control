# Cache Update Workflows

This document describes the automated GitHub Actions workflows that populate session cache files for the history page.

## Overview

Session cache files (`data/session_cache/YYYY-MM.json`) contain minimal session data for fast history page loading. Rather than querying ChargePoint API on every page visit, these workflows pre-populate cache files that are loaded directly from the GitHub repository.

## Workflows

### 1. Individual Session (Real-time)

**Workflow**: `collect-session-data.yml`  
**Trigger**: Dispatched by `monitor_sessions.py` when new session detected  
**Frequency**: Each charging session (~1 per day)

**Steps**:
1. `collect_session_data.py` - Collect 5 minutes of power samples
2. `classify_vehicle.py` - ML classification of vehicle
3. `fetch_session_details.py <session_id>` - Fetch ChargePoint metrics, cache to monthly file

**Result**: New session added to current month's cache immediately after session completes.

---

### 2. Weekly Current Month Update

**Workflow**: `update-cache.yml`  
**Trigger**: Cron schedule - Sundays at 8am UTC (midnight Pacific)  
**Command**: `fetch_session_details.py --current`

**Purpose**: Refresh current month's cache with all sessions from month start to now. Catches any sessions that might have been missed or need updates.

**Manual Trigger**: 
- Go to Actions → Update Session Cache → Run workflow
- Select mode: `current` (default)

---

### 3. Monthly Previous Month Closure

**Workflow**: `monthly-cache-update.yml`  
**Trigger**: Cron schedule - 2nd of each month at 10am UTC (2am Pacific)  
**Command**: `fetch_session_details.py --month YYYY-MM` (previous month)

**Purpose**: Fetch complete previous month after it ends. Ensures historical data is fully populated and correct.

**Manual Trigger**: Not typically needed (automatic on month rollover)

---

## Manual Workflow Options

### Update Cache (update-cache.yml)

**Modes**:
- `current`: Fetch current month up to now
- `last`: Fetch entire previous month
- `month`: Fetch specific month (requires YYYY-MM parameter)

**Use Cases**:
- **Current**: Force refresh if page shows incomplete data
- **Last**: Re-fetch previous month if there were issues
- **Month**: Backfill historical months (e.g., `2025-12`)

**How to Run**:
1. Go to GitHub Actions tab
2. Select "Update Session Cache" workflow
3. Click "Run workflow"
4. Select mode and optionally specify month
5. Click "Run workflow" button

---

## File Organization

```
data/
  session_cache/
    2025-12.json    # December 2025 (30-40 sessions)
    2026-01.json    # January 2026 (current month, growing)
```

Each file contains an array of minimal session objects:
```json
[
  {
    "session_id": "4751613101",
    "session_start_time": "2026-01-10T14:00:01+00:00",
    "session_end_time": "2026-01-10T22:30:15+00:00",
    "energy_kwh": 51.22,
    "vehicle": {
      "id": "serenity_equinox_2024",
      "confidence": 0.95
    }
  }
]
```

---

## Benefits

1. **Faster Page Loads**: History page doesn't wait for API calls
2. **Offline Capability**: Works even if ChargePoint API is down
3. **Audit Trail**: Git commits show exactly when cache was updated
4. **Automatic Maintenance**: Current month stays fresh, historical months finalized

---

## Troubleshooting

### History page shows "No data yet"
- Check if `data/session_cache/YYYY-MM.json` exists for current month
- Manually run `update-cache.yml` with mode `current`

### Missing sessions in current month
- Wait for Sunday weekly refresh (automatic)
- Or manually run `update-cache.yml` → mode: `current`

### Historical month incomplete
- Manually run `update-cache.yml` → mode: `month` → specify YYYY-MM

### Check workflow status
1. Go to GitHub Actions tab
2. Look for recent "Update Session Cache" or "Monthly Cache Update" runs
3. Check logs for any errors

---

## Related Documentation

- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Data file structures
- [SCHEMA.md](SCHEMA.md) - JSON schemas for session cache
- [.github/workflows/](../.github/workflows/) - Workflow definitions
