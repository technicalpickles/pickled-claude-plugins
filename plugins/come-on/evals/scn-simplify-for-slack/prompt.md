Here's your last reply. Simplify it for a Slack message to my team.

"So, looking at this from a few angles. First, the migration itself: we added the
column in a separate deploy, which is the safe pattern, and backfilled in batches
of 1,000, which took about 40 minutes in staging. Second, there's the question of
whether the old code path still reads the legacy column; I checked and it does,
in two places (orders_controller and the nightly export), so we can't drop it yet.
Third, rollout: the flag is on for 10% in production. Fourth, there's some
discussion to be had about whether the export should move to the new column first
or whether we wait for the controller. My overall take is that we're on track, the
backfill is done, and the remaining work is switching the two readers before we
drop the legacy column next week, with the export being the riskier one."
