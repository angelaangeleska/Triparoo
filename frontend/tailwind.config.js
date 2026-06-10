/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7f5',
          100: '#dceee8',
          200: '#b8ddd2',
          300: '#8cc4b4',
          400: '#5a9e8f',
          500: '#428576',
          600: '#336a5f',
          700: '#2b564e',
          800: '#254641',
          900: '#1e3a5f',
          950: '#152536',
        },
        sunset: {
          400: '#f0956e',
          500: '#e8734a',
          600: '#d4552a',
        },
        sand: {
          50: '#faf6f1',
          100: '#f3ebe0',
          200: '#e8d9c8',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
      boxShadow: {
        soft: '0 4px 24px -4px rgba(30, 58, 95, 0.08)',
        card: '0 8px 32px -8px rgba(30, 58, 95, 0.12)',
        glow: '0 0 40px -10px rgba(90, 158, 143, 0.35)',
      },
      backgroundImage: {
        'hero-gradient':
          'linear-gradient(135deg, rgba(30,58,95,0.92) 0%, rgba(66,133,118,0.85) 50%, rgba(232,115,74,0.75) 100%)',
        'mesh-gradient':
          'radial-gradient(at 40% 20%, rgba(90,158,143,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(232,115,74,0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(30,58,95,0.08) 0px, transparent 50%)',
      },
    },
  },
  plugins: [],
}
