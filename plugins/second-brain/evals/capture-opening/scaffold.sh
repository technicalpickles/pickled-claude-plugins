#!/usr/bin/env bash
# case.yaml paths must stay inside the case dir, so delegate to the shared scaffold.
# The same-subject roc-algorithm note is what capture must link to but never edit.
export WITH_SAME_SUBJECT_NOTE=1
source "$(dirname "${BASH_SOURCE[0]}")/../_shared/scaffold-vault.sh"
