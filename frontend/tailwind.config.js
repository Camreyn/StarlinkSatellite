/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#1b1b1f',
        paper: '#fbfaf7',
        orbit: '#0f766e',
        plasma: '#b45309',
        signal: '#be123c',
      },
    },
  },
  plugins: [],
};
