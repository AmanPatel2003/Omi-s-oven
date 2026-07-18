import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex w-full items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60",
          variant === "primary" &&
            "bg-crust-600 text-crust-50 hover:bg-crust-700",
          variant === "secondary" &&
            "bg-crust-100 text-crust-800 hover:bg-crust-200",
          className
        )}
        {...props}
      >
        {isLoading ? "Please wait…" : children}
      </button>
    );
  }
);
Button.displayName = "Button";
