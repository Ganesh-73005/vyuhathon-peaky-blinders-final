/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        background: "#09090B",
        foreground: "#FAFAFA",
        card: "#18181B",
        primary: "#22C55E",
        secondary: "#27272A",
        muted: "#27272A",
        "muted-foreground": "#A1A1AA",
        accent: "#F59E0B",
        destructive: "#EF4444",
        border: "#27272A",
        ring: "#22C55E"
      },
      fontFamily: {
        sans: ['Manrope', 'Inter', 'system-ui', 'sans-serif'],
        tamil: ['Noto Sans Tamil', 'sans-serif']
      }
    }
  },
  plugins: []
}
