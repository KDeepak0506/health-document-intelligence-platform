# IPS18 Frontend — Week 1

React + Vite. Covers: Login → Dashboard → Upload → Document List with live status.

## Setup

```bash
cd frontend
cp .env.example .env      # point VITE_API_BASE_URL at Deepak's backend
npm install
npm run dev               # http://localhost:5173
```

Backend must be running at the URL in `.env` (defaults to `http://localhost:8000/api/v1`).

## What's here

- `src/api/client.js` — axios instance. Attaches the JWT to every request, clears
  it on 401, and normalizes all errors into `{ status, code, message }` so
  components never touch raw axios errors.
- `src/api/auth.js`, `src/api/documents.js` — thin wrappers, one function per
  documented endpoint (`POST /auth/login`, `POST /documents`, `GET /documents`,
  `GET /documents/{id}/status`).
- `src/context/AuthContext.jsx` — holds the token in memory + localStorage,
  exposes `login()`, `logout()`, `isAuthenticated`.
- `src/components/ProtectedRoute.jsx` — redirects to `/login` if not authenticated.
- `src/pages/Login.jsx` — email/password form, shows a clear 401 vs. network error.
- `src/pages/Dashboard.jsx` — owns the document list state and a lightweight
  poller: any document still `Pending`/`Processing` gets its status re-fetched
  every 4s until it resolves, so users see progress without refreshing.
- `src/components/UploadForm.jsx` — drag/drop + file picker, validates type
  (PDF/JPG/JPEG/PNG) and a 20MB size cap client-side before hitting the API.
- `src/components/DocumentList.jsx` — status pills (Pending/Processing/
  Completed/Failed), newest upload gets a brief highlight animation.

## Known gaps / next steps for whoever picks this up

- No `/auth/register` UI yet — assumes accounts are seeded or created via
  Swagger for now. Add a Register page if self-signup is in scope.
- Polling is naive (interval per active doc, not WebSocket/SSE). Fine for
  week 1 volume; revisit if the pipeline gets slow or documents pile up.
- `patient_id` is not collected on upload yet — matches the backend's current
  optional field, add a selector once the Patients table/UI exists.
