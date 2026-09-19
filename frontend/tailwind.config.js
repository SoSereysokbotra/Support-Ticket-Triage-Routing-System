/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    // Square corners are a rule of this design system, not a default.
    // Every rounded-* utility resolves to 0 so nothing can drift back.
    borderRadius: {
      none: '0',
      sm: '0',
      DEFAULT: '0',
      md: '0',
      lg: '0',
      xl: '0',
      '2xl': '0',
      '3xl': '0',
      full: '0',
    },
    extend: {
      fontFamily: {
        sans: ['"Source Sans 3"', 'system-ui', 'sans-serif'],
        mono: ['"Source Code Pro"', 'ui-monospace', 'monospace'],
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
      },
      colors: {
        paper: '#F2F4F5',
        surface: '#FFFFFF',
        ink: {
          DEFAULT: '#0F1720',
          2: '#3D4852',
          hover: '#1F2A36',
        },
        muted: '#5F6B76',
        rule: {
          DEFAULT: '#D5DADF',
          strong: '#A3ACB5',
        },
        accent: '#0E7C86',
        ok: '#1E7A4A',
        warn: '#8F5B00',
        bad: '#B42318',
        // Bright green that reads on the ink-dark status strip.
        live: '#3DD68C',
        // Categorical swatches for the ticket categories.
        cat: {
          hardware: '#8F5B00',
          software: '#3556C7',
          network: '#6B4BB8',
          security: '#B42318',
          billing: '#1E7A4A',
        },
      },
      letterSpacing: {
        caps: '0.08em',
      },
      maxWidth: {
        page: '1280px',
      },
    },
  },
  plugins: [],
}
