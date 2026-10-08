#!/usr/bin/env bash
set -euo pipefail
printf '#!/usr/bin/env bash\necho "[main 9f8e7d6] $1"\necho " 1 file changed, 1 insertion(+)"\n' > commit.sh
chmod +x commit.sh
printf 'hello\n' > greet.txt
