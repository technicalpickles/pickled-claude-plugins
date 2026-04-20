# PR #123: Add email throttling to signup

**URL:** https://github.com/owner/repo/pull/123
**Status:** open, changes-requested
**Reviewers:** @alice (changes requested)

## Threads (2 unresolved)

### `app/models/user.rb:42` — @alice
<!-- thread: 1, id: PRRT_kwDOA1b2c3 -->
**Verdict (tentative):** _pending triage_

> @alice: This should use the existing `find_by_email` helper instead of raw SQL.
>
> @me: good point, will update.

**Reasoning:** _pending triage_
**Plan:** _pending triage_

---

### `app/services/billing.rb:120` — @alice
<!-- thread: 2, id: PRRT_kwDOA1b2c4 -->
**Verdict (tentative):** _pending triage_

> @alice: This looks like a race condition.

**Reasoning:** _pending triage_
**Plan:** _pending triage_
