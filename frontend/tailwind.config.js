/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          dark: '#111111',
          light: '#F6F6F3',
        },
        text: {
          light: '#FFFFFF',
          dark: '#222222',
        },
        accent: '#D4B15A',
      },
      borderRadius: {
        md: '8px',
        lg: '12px',
      },
      spacing: {
        sm: '16px',
        md: '24px',
        lg: '48px',
        xl: '80px',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Lora', 'ui-serif', 'Georgia', 'serif'],
      },
      boxShadow: {
        soft: '0 8px 24px rgba(0,0,0,0.24)',
      },
      screens: {
        xs: '480px',
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
      },
    },
  },
  plugins: [],
};

