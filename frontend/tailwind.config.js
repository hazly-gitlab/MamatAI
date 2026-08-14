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
          dark: '#05070c',
          card: '#0b1120',
          border: '#1e293b',
          cyan: '#06b6d4',
          neon: '#00f2fe',
        }
      }
    },
  },
  plugins: [],
}
