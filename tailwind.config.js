/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        ink:   { 900: '#0F211D', 800: '#16302A', 700: '#1E3B33', 600: '#2A4E44' },
        paper: { 50: '#F6F5F0', 100: '#EFEEE7', 200: '#E4E2D8' },
        brand: { 400: '#FDBB3D', 500: '#FCAB10', 600: '#E0960C', 700: '#A66E08' },
        pine:  { 500: '#3E7C6A', 600: '#336657', 700: '#2A5548' },
        rust:  { 500: '#C1483A', 600: '#A83B2F' },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      boxShadow: {
        ticket: '0 20px 40px -18px rgba(15, 33, 29, 0.35)',
      },
    },
  },
  plugins: [],
}