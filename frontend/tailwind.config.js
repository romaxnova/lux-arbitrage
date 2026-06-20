/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(222 47% 6%)",
        foreground: "hsl(210 40% 98%)",
        card: "hsl(222 47% 9%)",
        border: "hsl(217 33% 17%)",
        muted: "hsl(215 20% 65%)",
        accent: "hsl(262 83% 58%)",
        buy: "hsl(142 71% 45%)",
        watch: "hsl(38 92% 50%)",
        skip: "hsl(0 72% 51%)",
      },
      fontFamily: {
        sans: ["var(--font-geist)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
