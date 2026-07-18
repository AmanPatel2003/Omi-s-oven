import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface Toast {
  id: string;
  message: string;
  variant: "success" | "error" | "info";
}

interface UiState {
  isCartDrawerOpen: boolean;
  activeModal: string | null;
  toasts: Toast[];
}

const initialState: UiState = {
  isCartDrawerOpen: false,
  activeModal: null,
  toasts: [],
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    openCartDrawer: (state) => {
      state.isCartDrawerOpen = true;
    },
    closeCartDrawer: (state) => {
      state.isCartDrawerOpen = false;
    },
    openModal: (state, action: PayloadAction<string>) => {
      state.activeModal = action.payload;
    },
    closeModal: (state) => {
      state.activeModal = null;
    },
    pushToast: (state, action: PayloadAction<Omit<Toast, "id">>) => {
      state.toasts.push({ id: crypto.randomUUID(), ...action.payload });
    },
    dismissToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
  },
});

export const {
  openCartDrawer,
  closeCartDrawer,
  openModal,
  closeModal,
  pushToast,
  dismissToast,
} = uiSlice.actions;
export default uiSlice.reducer;
