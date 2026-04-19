/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/views/**/*.twig',
    './public/**/*.php',
  ],
  safelist: [
    // Classes générées dynamiquement (Alpine, JS)
    'in-view',
    'active',
    'cal-l1', 'cal-l2', 'cal-l3', 'cal-l4',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        body: ['DM Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
