# frontend/tracker
OWNER: M2 (Application Tracker)

CareerTrack's job board, tracker, preparation tools, and admin workspace are served by FastAPI at `/tracker/`.

It uses the live JSON authentication and tracker APIs; no separate build step is needed.
The page stores the bearer token in browser local storage. Sign out clears it.

The backend stores document links and metadata. Uploading binaries is not part of this initial UI.
