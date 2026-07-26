import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface Toast {
  id: string;
  message: string;
  variant: "success" | "error" | "info";
}

interface UiState {
  // Named to match the Cart module spec exactly ("uiSlice's isCartOpen
  // boolean") — read by both the header's cart icon and CartDrawer.
  isCartOpen: boolean;
  activeModal: string | null;
  toasts: Toast[];
}

const initialState: UiState = {
  isCartOpen: false,
  activeModal: null,
  toasts: [],
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    openCart: (state) => {
      state.isCartOpen = true;
    },
    closeCart: (state) => {
      state.isCartOpen = false;
    },
    toggleCart: (state) => {
      state.isCartOpen = !state.isCartOpen;
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
  openCart,
  closeCart,
  toggleCart,
  openModal,
  closeModal,
  pushToast,
  dismissToast,
} = uiSlice.actions;
export default uiSlice.reducer;
