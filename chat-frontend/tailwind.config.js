/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        wb: {
          blue:   '#0071CE',
          navy:   '#003D7A',
          teal:   '#009FDA',
          light:  '#EBF5FD',
          gold:   '#F5A623',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Arial', 'Helvetica', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
