/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#6C63FF',
        'primary-dark': '#5A52D5',
        surface: '#1E1E2E',
        'surface-2': '#2A2A3E',
        'surface-3': '#313145',
        border: '#3D3D5C',
        'text-primary': '#E0E0FF',
        'text-secondary': '#9898B8',
        success: '#50FA7B',
        warning: '#FFB86C',
        error: '#FF5555',
        info: '#8BE9FD',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}