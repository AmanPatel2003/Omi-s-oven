import type { Metadata } from "next";
import { Providers } from "@/app/providers";
import "./globals.css";
import { ToastContainer } from "@/components/shared/ToastContainer";

export const metadata: Metadata = {
  title: "The Bakery",
  description: "Fresh bakes, custom cakes, delivered.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-crust-50 text-crust-900 font-body antialiased">
        <Providers>
          {children}
          <ToastContainer />
        </Providers>
      </body>
    </html>
  );
}
