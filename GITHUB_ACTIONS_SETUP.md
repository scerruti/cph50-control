# GitHub Actions Setup Guide

## Overview

This project uses GitHub Actions to automate CPH50 EV charger control. The workflow runs twice daily at 1:00 PM and 2:00 PM UTC (covering 6:00 AM PST year-round, handling DST transitions automatically).

## Prerequisites

1. GitHub account with this repository
2. ChargePoint account credentials
3. ChargePoint station ID

## Setup Steps

### 1. Create GitHub Repository

If you haven't already:

```bash
cd /Users/scerruti/cph50\ control
git init
git add .
git commit -m "Initial commit: EV charging automation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cph50-control.git
git push -u origin main
```

### 2. Configure GitHub Secrets

Navigate to your GitHub repository:
- Go to **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret**

Add these three secrets:

| Secret Name | Value |
|------------|-------|
| `CP_USERNAME` | `scerruti` |
| `CP_PASSWORD` | `4ndZ!^Vy?5NbNuT` |
| `CP_STATION_ID` | `12048111` |

**Important:** Never commit these values to the repository. They should only exist in GitHub Secrets.

### 3. Enable GitHub Actions

- Go to **Actions** tab in your repository
- If prompted, click **I understand my workflows, go ahead and enable them**

### 4. Test the Workflow

#### Option A: Wait for Scheduled Run
The workflow will automatically run at:
- 1:00 PM UTC (5 AM PST / 6 AM PDT)
- 2:00 PM UTC (6 AM PST / 7 AM PDT)

The script checks the local time and only charges when it's 6 AM Pacific.

#### Option B: Manual Trigger (Recommended for Testing)
1. Go to **Actions** tab
2. Click **EV Charging Automation** workflow
3. Click **Run workflow** dropdown
4. Click **Run workflow** button

This triggers the job immediately regardless of time (useful for testing connectivity).

## How It Works

1. **Cron Schedule**: GitHub Actions triggers the workflow at 1:00 PM and 2:00 PM UTC daily
2. **Time Check**: Python script checks if current time in `America/Los_Angeles` timezone is 6 AM (hour == 6)
3. **Exit Early**: If not 6 AM, script exits with status 0 (no error)
4. **Charge Sequence** (at 6 AM):
   - Authenticate to ChargePoint
   - Fetch home chargers
   - Check charger status (connected, plugged_in)
   - Start charging session
5. **Results**: Logs appear in the Actions run details

## Monitoring

### View Logs
1. Go to **Actions** tab
2. Click on a workflow run
3. Click on the **charge** job
4. Expand any step to see detailed logs

### Expected Output (Not 6 AM)
```
ℹ️  Not charging time (current hour: 14, target: 6)
Exiting normally
```

### Expected Output (Success at 6 AM)
```
🎯 It's 6 AM PST - initiating charge sequence...
🔐 Authenticating as scerruti...
✓ Authentication successful
🔍 Fetching home chargers...
✓ Found charger: 12048111
📊 Charger Status:
   Connected: True
   Plugged In: True
   Model: CPH50
⚡ Starting charging session for station 12048111...
✅ SUCCESS: Charging session started!
```

### Expected Output (Charger Offline)
```
⚠️  WARNING: Charger is offline (not connected to network)
   Charging cannot start until charger reconnects
❌ Charging automation failed
```

## Troubleshooting

### Workflow Not Running
- Check that GitHub Actions is enabled in repository settings
- Verify cron syntax in `.github/workflows/charge-ev.yml`
- Check for any GitHub Actions service outages

### Authentication Failures
- Verify secrets are set correctly (no extra spaces)
- Check if ChargePoint account is locked (too many failed attempts)
- Test credentials manually using local Python script

### Charger Offline
- Restart CPH50 (unplug for 30 seconds, replug)
- Check WiFi connection (open ChargePoint app to verify)
- View charger status in ChargePoint web interface

### Wrong Timezone
- Script uses `America/Los_Angeles` timezone automatically
- DST transitions are handled by `zoneinfo` library
- No configuration needed

## Local Testing

Test the script locally before relying on GitHub Actions:

```bash
cd /Users/scerruti/cph50\ control
source test_env/bin/activate
export CP_USERNAME="scerruti"
export CP_PASSWORD="4ndZ!^Vy?5NbNuT"
export CP_STATION_ID="12048111"
python charge_github.py
```

## Cost

GitHub Actions provides **2,000 minutes/month** of free runtime for public repositories and **500 minutes/month** for private repositories. This workflow uses approximately:
- ~2 minutes per run
- 2 runs per day
- ~60 runs per month
- **~120 minutes/month total**

Well within the free tier limits.

## Advantages Over Other Solutions

✅ **Free** (no hosting costs)  
✅ **No WAF blocking** (GitHub Actions IPs are widely trusted)  
✅ **Built-in logging** (view all run history in Actions tab)  
✅ **Secure secrets** (encrypted at rest)  
✅ **Easy monitoring** (email notifications on failure)  
✅ **Version controlled** (workflow changes tracked in git)  

## Next Steps

1. ✅ Set up GitHub Secrets
2. ✅ Enable GitHub Actions
3. ⏳ Test with manual workflow trigger
4. ⏳ Verify charger comes online (restart CPH50 if needed)
5. ⏳ Wait for 6 AM PST run to confirm automatic charging
6. ⏳ Monitor Actions logs for any issues

## Support

If issues persist:
- Check charger status manually: Open ChargePoint app/website
- Review GitHub Actions logs for detailed error messages
- Verify all secrets are set correctly
- Ensure vehicle is plugged in and CPH50 is online
