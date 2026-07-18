// ---------------------------------------------------------------------------
// Generic envelope every backend endpoint responds with:
//   { success: boolean, data: T, message: string }
// RTK Query's `transformResponse` unwraps this per-endpoint so components
// only ever see `T`. Keep this type in sync with the backend's response
// wrapper — if the backend changes the envelope shape, this is the one
// place to update.
// ---------------------------------------------------------------------------
export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
}

// Shape returned by FastAPI/Pydantic on a 422 validation error.
export interface ValidationErrorResponse {
  detail: Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}

export type UserRole = "customer" | "staff" | "admin";

// Base fields present regardless of how the user authenticated.
interface BaseUser {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: UserRole;
  createdAt: string;
}

// Email/password registered user — no `picture`.
export interface EmailUser extends BaseUser {
  authProvider: "email";
}

// Google-authenticated user — has `picture`, provider is fixed.
export interface GoogleUser extends BaseUser {
  authProvider: "google";
  picture: string;
}

// The backend's /auth/login and /auth/google-login responses use slightly
// different `user` shapes (see build-prompt note under Auth Module). Model
// both as a discriminated union on `authProvider` rather than optional
// fields everywhere, so a missing `picture` is a type error, not a runtime
// surprise.
export type User = EmailUser | GoogleUser;

export interface AuthTokens {
  accessToken: string;
  // The refresh token itself never reaches client JS — it's set directly as
  // an httpOnly cookie by the Route Handler. It is NOT part of this type on
  // purpose; if you find yourself adding `refreshToken` here, stop — that
  // defeats the point of the httpOnly cookie strategy.
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export interface RegisterResponse extends AuthTokens {
  user: User;
}

export interface RefreshResponse extends AuthTokens {
  user: User;
}

export interface LoginRequest {
  identifier: string; // email or phone
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  phone: string;
  password: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}
