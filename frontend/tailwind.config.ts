import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        crust: {
          50: "#FBF6EE",
          100: "#F4E9D6",
          200: "#E6CFA8",
          300: "#D6AE72",
          400: "#C68E4B",
          500: "#A9702F",
          600: "#8A5824",
          700: "#6B421C",
          800: "#4D2F15",
          900: "#33200E",
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
      },
      borderRadius: {
        xl: "0.875rem",
      },
    },
  },
  plugins: [],
};

export default config;
