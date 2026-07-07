import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Ice Cave & Sky
        'deep-blue': '#0a1e3d',
        'sky-blue': '#1e4d8b',
        'ice-blue': '#4d9fff',

        // Warm Accents
        'warm-orange': '#ff8c42',
        'warm-pink': '#ff6b9d',
        'candle-glow': '#ff6b42',

        // Aurora
        'aurora-blue': '#4d9fff',
        'aurora-purple': '#9d4dff',
        'aurora-green': '#4dffaa',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(--radius - 4px)',
      },
    },
  },
  plugins: [],
};

export default config;