Session so far (we did this work together, and I am handing it off):

We are in a small Python service called ratelimit-demo, on branch feat/token-bucket.

Done and committed: limiter.py has a TokenBucket class (capacity, refill_per_sec).

In progress, uncommitted: test_limiter.py::test_refill_after_wait fails because the bucket refills from time.time() and the test patches time.monotonic. I decided to switch the bucket to time.monotonic() so wall-clock changes cannot break refill. I have not made that edit yet.

I read server.py and config.yaml to see where the limiter will plug in, and changed neither.

Decisions: token bucket over sliding window (cheaper, and bursts are fine here). Monotonic clock, not wall clock.

Next: (1) make the refill fix and get the tests green, (2) wire the limiter into the request middleware in server.py, (3) add a short section to the README.

Open question: key the bucket per client IP or per API key? It blocks step 2, not step 1. Ask me when you get there.

House rules for whoever continues: run tests with `make test`, never bare pytest, because the Makefile sets up the environment. Do not push anything, I will review locally first. Commit messages use conventional commits (that is already in CLAUDE.md).

I am switching to a new session now.
