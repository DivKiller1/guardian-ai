/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f172a", // Slate 900
        foreground: "#f8fafc", // Slate 50
        card: "#1e293b",       // Slate 800
        accent: "#3b82f6",     // Blue 500
        border: "#334155",     // Slate 700
        danger: "#ef4444",
        success: "#22c55e",
        warning: "#f59e0b",
      },
    },
  },
  plugins: [],
}
