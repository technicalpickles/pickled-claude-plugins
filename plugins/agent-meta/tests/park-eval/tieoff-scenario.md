Session so far (we did this together):

This repo is a tiny Python CLI called fetcher, with no remote. We created a worktree for branch feat/fetch next to the repo (../wt-fetch), implemented fetch there, and I merged feat/fetch into main locally. Nothing else uses that worktree. You also updated README.md's status line on main, which isn't committed yet.

While working we noticed fetch has no retry on network errors. We said we'd handle that later, not in this change.
