/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'brand': {
          50: '#f0f0ff',
          100: '#e6e6ff',
          500: '#7C4DFF',
          600: '#6A3BFF',
          700: '#5835cc',
          900: '#2d1a66'
        },
        'surface': {
          DEFAULT: '#121A2B',
          2: '#151F34',
          3: '#1a2332'
        },
        'dark': {
          bg: '#0B1020',
          text: '#E6E6F0',
          muted: '#9AA4B2'
        }
      },
      fontFamily: {
        'inter': ['Inter', 'system-ui', 'sans-serif']
      },
      boxShadow: {
        'modern': '0 10px 30px rgba(0,0,0,0.35)',
        'ring': '0 0 0 3px rgba(124, 77, 255, 0.45)'
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-in-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      }
    },
  },
  plugins: [],
}