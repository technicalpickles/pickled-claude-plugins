# Baseline Test - Scenario 1: Urgent CLI Build

## Test Date
2025-01-25

## Scenario
Build health check CLI under time pressure (15 minutes, production down)

## Agent Choices (WITHOUT skill)

### ✅ What They Got Right (High Impact, Low Effort)
1. **--help text with examples** - Explicitly mentioned "users might not know flags"
2. **Proper exit codes (0/1)** - Critical for CI/CD
3. **Clear error messages** - Distinguishes timeout, connection failure, wrong status
4. **Configurable timeout** - Prevents CI hanging
5. **Quiet mode** - Scripts that only care about exit codes

### ⚠️ What's Interesting
- Used emoji (✓ ✗) in output - visual but not explicitly designed
- URL validation - safety feature, low effort
- Examples in --help epilog - good discoverability
- Proper argparse usage with descriptions

### ❌ What They Missed/Could Improve
1. **No --no-color flag** - Used emojis/symbols but no accessibility option
2. **No explicit "loading" feedback** - Silent during HTTP request (could be slow)
3. **Error messages could suggest fixes** - "Connection failed" vs "Connection failed. Check network or try --timeout"
4. **Help text doesn't mention exit codes** - CI/CD users need to know 0=success, 1=failure

### 🤔 Priority Understanding
**Good:**
- Focused on exit codes immediately (CI/CD requirement)
- Added --help without being prompted
- Clear error messages over polish

**Could be better:**
- Didn't consider progress feedback during slow requests
- Accessibility (--no-color) not considered even though using symbols
- Error messages miss opportunity to guide next steps

## Rationalizations Used
1. "Quick to write" - chose Python for speed
2. "For urgent production check, one attempt is faster" - skipped retry
3. "Can add in v2" - deferred non-critical features
4. "Not in requirements" - focused scope

## Conclusion
Agent had good intuition about high-impact features (help, exit codes, error messages) but:
- **Missing**: Progress feedback, accessibility, actionable error guidance
- **Didn't explicitly prioritize** - seemed to know good patterns but didn't articulate priority framework
- **No systematic check** - worked from intuition, not a checklist

## What Skill Should Teach
1. **Explicit priority framework**: Help > Exit codes > Error messages > Feedback > Color
2. **Quick wins checklist** under time pressure
3. **Progress feedback matters** even in simple CLIs (HTTP requests can be slow)
4. **Error messages should suggest fixes** (actionable, not just descriptive)
5. **Accessibility is low-effort** (--no-color flag = 2 minutes)
