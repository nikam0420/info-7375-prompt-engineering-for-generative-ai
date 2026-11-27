# Premortem

Written before executing the demonstration on November 27, 2026. Both watchers can read the same notes revision, compute different entries, and each submit a complete replacement. Without comparing the expected version, the second write can erase the first watcher's entries. The demonstration will force both watchers to read before either writes. I expect the stale write to be rejected, the notes file bytes to remain unchanged by the rejected write, and a fresh merge to preserve both watchers' entries. A fixture will also include instruction-like text in a posting description. It should remain a string in JSON notes and have no ability to select a tool or change the revision.

See generated evidence for the observed outcome.

## Observed outcome

Both seeded days reproduced the conflict. The rejected writes expected revisions 0 and 2 and encountered revisions 1 and 3. Each rejection left notes bytes unchanged. One merge per day advanced the notes to revisions 2 and 4 and preserved both watcher entries. The day-one state retained the instruction-like description verbatim while the notes revision advanced through commits. See evidence/replay/day1-conflict.json, day2-conflict.json and day1-state.json.
