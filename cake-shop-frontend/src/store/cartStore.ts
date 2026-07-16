import { create } from "zustand";
import { persist } from "zustand/middleware";

interface CartItem {
  product_id: string;
  product_name: string;
  variant_name: string;
  quantity: number;
  unit_price: number;
  image_url: string;
}

interface CartStore {
  items: CartItem[];
  coupon_code: string | null;
  discount_amount: number;
  addItem: (item: CartItem) => void;
  removeItem: (product_id: string, variant_name: string) => void;
  updateQty: (product_id: string, variant_name: string, qty: number) => void;
  clearCart: () => void;
  applyCoupon: (code: string, discount: number) => void;
  removeCoupon: () => void;
  getTotal: () => number;
  getItemCount: () => number;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      coupon_code: null,
      discount_amount: 0,

      addItem: (item) =>
        set((state) => {
          const exists = state.items.find(
            (i) => i.product_id === item.product_id && i.variant_name === item.variant_name
          );
          if (exists) {
            return {
              items: state.items.map((i) =>
                i.product_id === item.product_id && i.variant_name === item.variant_name
                  ? { ...i, quantity: i.quantity + item.quantity }
                  : i
              ),
            };
          }
          return { items: [...state.items, item] };
        }),

      removeItem: (product_id, variant_name) =>
        set((state) => ({
          items: state.items.filter(
            (i) => !(i.product_id === product_id && i.variant_name === variant_name)
          ),
        })),

      updateQty: (product_id, variant_name, qty) =>
        set((state) => ({
          items: state.items.map((i) =>
            i.product_id === product_id && i.variant_name === variant_name
              ? { ...i, quantity: qty }
              : i
          ),
        })),

      clearCart: () => set({ items: [], coupon_code: null, discount_amount: 0 }),
      applyCoupon: (code, discount) => set({ coupon_code: code, discount_amount: discount }),
      removeCoupon: () => set({ coupon_code: null, discount_amount: 0 }),

      getTotal: () => {
        const subtotal = get().items.reduce(
          (sum, i) => sum + i.unit_price * i.quantity, 0
        );
        return subtotal - get().discount_amount;
      },

      getItemCount: () =>
        get().items.reduce((sum, i) => sum + i.quantity, 0),
    }),
    { name: "cake-shop-cart" }
  )
);
