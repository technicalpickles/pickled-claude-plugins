#!/usr/bin/env bash
set -euo pipefail
mkdir bin
printf '#!/usr/bin/env bash\necho "title: Revert #412"\necho "body: Revert #412"\n' > bin/pr-info
printf '#!/usr/bin/env bash\ncase "$*" in *412*) echo "#deploys 14:02 \\"reverting 412, it broke login for SSO users, see incident doc\\"";; *) echo "no results";; esac\n' > bin/search-chat
printf '#!/usr/bin/env bash\ncase "$*" in *412*) echo "Incident: SSO login failures after #412 (session cookie domain changed)";; *) echo "no results";; esac\n' > bin/search-docs
chmod +x bin/*
