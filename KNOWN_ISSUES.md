# Known Issues

## GitHub Authentication (Personal Access Token)

**Issue**: Authentication uses GitHub Personal Access Tokens (PATs) stored in browser localStorage - temporary solution pending proper OAuth2 implementation.

**Current Implementation**:
- Users manually paste GitHub PAT into history page
- Token stored in `localStorage` (persists across browser sessions)
- Checked against GitHub API to verify collaborator status on `scerruti/cph50-control`
- Only contributors can access admin features (future)

**Security Concerns**:
- ⚠️ PAT stored in localStorage - accessible to XSS attacks
- ⚠️ Token visible in browser dev tools
- ⚠️ No automatic token refresh or expiration
- ⚠️ Requires user to manually create and manage tokens

**Why This Approach (Temporary)**:
- No backend token exchange server needed yet
- Simple to implement for single-user development
- Sufficient for current use case (only you access admin features)

**Future Solution - OAuth2 Flow**:
- User clicks "Login with GitHub"
- Redirects to GitHub OAuth authorize page
- Backend securely exchanges code for access token
- Token stored in secure HTTP-only cookie
- No PAT storage in localStorage
- Automatic expiration and refresh handling

**Roadmap**:
1. ✅ Current: PAT-based auth (working, limited security)
2. ⏳ Phase 2: OAuth2 with backend token exchange
3. ⏳ Phase 3: Multi-user permissions model

**Mitigation (Current)**:
- Only share repo link with trusted users
- Regenerate/revoke PAT if compromised
- Consider repo private if security is critical
- Monitor for unauthorized commits in git log

**Status**: Known limitation; acceptable for single-developer setup. Upgrade to OAuth2 when adding multi-user features.

---

## Daylight Saving Time Transitions

**Issue**: During DST transitions (spring forward and fall back), the history page may display incorrectly:
- **Spring Forward** (March 2nd, 2025): Hour 2:00-2:59 AM doesn't exist. Sessions during this period may display with incorrect hour labels or gaps.
- **Fall Back** (November 1st, 2025): Hour 1:00-1:59 AM occurs twice. Sessions may be assigned to the wrong occurrence.

**Impact**: 
- Day view may show missing or duplicate hours on DST transition dates
- Session timestamps converted to `America/Los_Angeles` timezone may be off by 1 hour near transitions
- Month and year views are less affected since they aggregate across days

**Root Cause**: JavaScript's `Date` object and `toLocaleString()` with timezone handling doesn't perfectly account for historical and future DST rules in all edge cases.

**Potential Solution**:
- Use a robust timezone library (e.g., `date-fns-tz`, `day.js` with `utc` and `timezone` plugins) instead of browser's built-in timezone conversion
- Convert UTC timestamps on the server side before sending to client
- Or: Accept the minor display issue on 2 days per year as acceptable trade-off vs. added complexity

**Status**: Low priority; affects 2 days per year for display purposes only. Data is stored correctly in UTC.

---

## Midnight-Spanning Sessions Energy Attribution

**Issue**: Sessions that cross midnight are attributed proportionally using vehicle's average charging rate, which may not reflect actual charging curve behavior.

**Current Implementation**:
- Uses fixed average charging rate from `vehicle_config.json` (e.g., 8.5 kW)
- Day 0 energy = (time in day 0) × avg_rate
- Day 1 energy = total_energy - day_0_energy

**Known Inaccuracy**:
- Charging rate typically declines over time (taper curve near full battery)
- Session start may have higher power draw than average
- Session end often shows reduced power as battery approaches full

**Impact**: 
- Energy attribution between days may be off by 5-15% for midnight-spanning sessions
- Affects day-view aggregates when sessions cross midnight
- Month/year views less affected (same total energy, just different daily breakdown)

**Potential Solution**:
- Analyze historical charging curves from power_samples data
- Develop time-weighted formula (e.g., exponential decay model)
- Or: Use actual power samples to calculate per-minute energy if available

**Status**: Low priority; most sessions complete within a single day. Documented for future enhancement.

---

## Future Enhancements

- [ ] Session file discovery should scan directory recursively rather than using hardcoded file list
- [ ] Add ability to manually upload/import session data from ChargePoint exports
- [ ] Export session history as CSV
- [ ] Add session search/filter by date range picker (currently: arrow buttons only)
