import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { User } from "@/types/api";

interface AuthState {
  user: User | null;
  access_token: string | null;
  isAuthenticated: boolean;
  /** True while /api/auth/session is being called on app load. */
  isHydrating: boolean;
}

const initialState: AuthState = {
  user: null,
  access_token: null,
  isAuthenticated: false,
  // Starts true: the root Providers component calls /api/auth/session on
  // mount before anything renders behind an auth check, to avoid a flash of
  // logged-out UI while the httpOnly-cookie refresh is in flight.
  isHydrating: true,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user: User; access_token: string }>,
    ) => {
      state.user = action.payload.user;
      state.access_token = action.payload.access_token;
      state.isAuthenticated = true;
    },
    setHydrated: (state) => {
      state.isHydrating = false;
    },
    logout: (state) => {
      state.user = null;
      state.access_token = null;
      state.isAuthenticated = false;
    },
  },
});

export const { setCredentials, setHydrated, logout } = authSlice.actions;
export default authSlice.reducer;
