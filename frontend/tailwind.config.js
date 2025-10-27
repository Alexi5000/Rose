/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
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
        
        // UI
        'white-transparent': 'rgba(255, 255, 255, 0.1)',
        'white-border': 'rgba(255, 255, 255, 0.3)',
      },
      backgroundImage: {
        'sky-gradient': 'linear-gradient(to bottom, #0a1e3d 0%, #1e4d8b 40%, #ff6b9d 70%, #ff8c42 100%)',
        'water-gradient': 'linear-gradient(to top, #0a1e3d 0%, #4d9fff 50%, #ff8c42 100%)',
      },
      screens: {
        'mobile': '768px',
        'tablet': '1024px',
        'desktop': '1440px',
        'ultrawide': '1920px',
      },
      letterSpacing: {
        'widest': '0.2em',
      },
    },
  },
  plugins: [],
}
