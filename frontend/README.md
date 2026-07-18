# Bakery App — Module 1: Auth

Frontend for the Auth module only (Section 1 of the build prompt), built on the
project skeleton from Section 0. Later modules (products, cart, orders,
payments, admin/staff panels) are not implemented here — this hands off
cleanly for the next module to build on `store/api/baseApi.ts` and
`hooks/useAuth.ts`.

## Run it

```bash
npm install
cp .env.local.example .env.local   # point API_URL / NEXT_PUBLIC_API_URL at your backend
npm run dev
```

Needs a running backend exposing the routes listed below. Nothing here was
run against a live backend — install/build were not executed in this
environment (no network access), so treat this as reviewed-but-unverified
and run `npm run build` yourself before shipping.

## Token strategy, concretely

The build prompt asks for: access token in memory only, refresh token in an
httpOnly cookie set by a Route Handler that proxies the backend. Implementing
that literally forces a specific shape, worth spelling out since it's easy to
get subtly wrong:

- **`store/api/baseApi.ts`** talks to the real backend
  (`NEXT_PUBLIC_API_URL`) for everything, with the access token as a Bearer
  header. It never sends cookies to the backend.
- **`login`, `register`, `logout`** (in `store/api/authApi.ts`) do **not**
  call the backend directly. They call this app's own
  `/api/auth/login|register|logout` Route Handlers. Those handlers are what
  actually talk to the backend, and they're the only code that ever sees the
  refresh token — they strip it out of the backend's response before
  forwarding anything to the browser, and set it as an httpOnly cookie
  scoped to the Next.js origin instead.
- **`/api/auth/refresh`** is a same-origin Route Handler. Because it's
  same-origin, the browser attaches the httpOnly cookie automatically — no
  client JS ever reads it. `baseApi`'s 401-retry logic calls this route, not
  the backend, for exactly that reason.
- **`/api/auth/session`** (GET) does the same exchange, called once on app
  load from `app/providers.tsx` to hydrate Redux before anything renders
  behind an auth check.

If you're adding a new auth-adjacent feature and are tempted to call the
backend directly from the client for anything involving the refresh token,
that's the tell you should be adding a Route Handler instead.

## Backend routes this expects

`POST /auth/register`, `POST /auth/login`, `POST /auth/google-login` (typed,
not yet wired to a UI button — add a "Continue with Google" button on the
login page calling this the same way `login` is called),
`POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`,
`POST /auth/change-password`.

Assumed response envelope: `{ success, data, message }`, with `data`
including `refreshToken` on login/register/refresh (stripped by the Route
Handlers before reaching the browser) and a `role` claim on the JWT that the
real backend endpoints check for authorization — middleware.ts only checks
cookie *presence*, not role, by design (see the comment there).

## Not yet done / left for later modules

- Google login button (types exist in `types/api.ts` as `GoogleUser`, no UI yet)
- Toasts aren't wired to any component yet (`uiSlice` has the actions, nothing dispatches them)
- `shadcn/ui` isn't installed — `Button`/`Field` here are minimal hand-rolled
  primitives so Module 1 doesn't block on a shadcn init; swap them out (or
  keep them, they're intentionally simple) when Module 2 needs dialogs/toasts
