/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          bg: '#0b0f19',
          card: '#0f172a',
          accent: '#06b6d4',
          danger: '#ef4444',
        }
      }
    },
  },
  plugins: [],
}