# CAMARA API Status

| API | Status | Notes |
|---|---|---|
| Location Verification v0.2.0 | Live, working | Tested via Nokia sandbox playground. Device +99999991001 -> TRUE. Device +99999991000 -> FALSE. Device +99999990400 -> 500 error (not wired for this endpoint). |
| Device Reachability Status v1.1.0 | Live, working | Tested both branches: +99999991000 -> reachable=true (connectivity: SMS). +99999991003 -> reachable=false. Note: real response shape has a connectivity array, not the roaming field the initial code assumed - needs a small fix in camara/client.py. || SIM Swap v1.0.0 | Live, working | Tested both branches: +99999991000 -> swapped=true. +99999991001 -> swapped=false. |