import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { User } from "@/types/api";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  /** True while /api/auth/session is being called on app load. */
  isHydrating: boolean;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
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
      action: PayloadAction<{ user: User; accessToken: string }>
    ) => {
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.isAuthenticated = true;
    },
    setHydrated: (state) => {
      state.isHydrating = false;
    },
    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
    },
  },
});

export const { setCredentials, setHydrated, logout } = authSlice.actions;
export default authSlice.reducer;
