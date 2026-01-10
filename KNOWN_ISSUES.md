# Known Issues

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

## Future Enhancements

- [ ] Session file discovery should scan directory recursively rather than using hardcoded file list
- [ ] Add ability to manually upload/import session data from ChargePoint exports
- [ ] Export session history as CSV
- [ ] Add session search/filter by date range picker (currently: arrow buttons only)
