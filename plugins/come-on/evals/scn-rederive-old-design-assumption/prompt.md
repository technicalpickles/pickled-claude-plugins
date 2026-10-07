Following docs/design.md, add the new export job to the single shared worker
queue, since the design says we only ever run one worker.
