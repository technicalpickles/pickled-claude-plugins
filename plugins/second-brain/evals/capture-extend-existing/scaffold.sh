#!/usr/bin/env bash
# case.yaml paths must stay inside the case dir, so delegate to the shared scaffold.
# The roc-algorithm stub is the existing note this case is about.
export WITH_SAME_SUBJECT_NOTE=1
source "$(dirname "${BASH_SOURCE[0]}")/../_shared/scaffold-vault.sh"
