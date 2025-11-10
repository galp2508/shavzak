/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        military: {
          50: '#f0f9f4',
          100: '#daf1e4',
          200: '#b8e3cd',
          300: '#8acfae',
          400: '#57b389',
          500: '#34996e',
          600: '#257b58',
          700: '#1e6248',
          800: '#1a4e3a',
          900: '#164030',
        },
        idf: {
          green: '#34996e',
          darkgreen: '#1e6248',
          gold: '#D4AF37',
          red: '#BF092F',
        }
      },
      fontFamily: {
        hebrew: ['Rubik', 'Assistant', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
