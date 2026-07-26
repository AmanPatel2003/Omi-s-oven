import { Header } from "@/components/layout/Header";
import { CartDrawer } from "@/components/cart/CartDrawer";

export default function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Header />
      {children}
      <CartDrawer />
    </>
  );
}
