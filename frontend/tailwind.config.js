/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        brand: {
          cyan: '#06b6d4',
          fuchsia: '#c026d3',
          amber: '#f59e0b',
        },
        surface: {
          DEFAULT: 'hsl(var(--surface))',
          elevated: 'hsl(var(--surface-elevated))',
          border: 'hsl(var(--surface-border))',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'mesh-gradient': 'radial-gradient(ellipse 80% 80% at 50% -20%, rgba(6,182,212,0.12), transparent), radial-gradient(ellipse 60% 60% at 80% 80%, rgba(192,38,211,0.10), transparent)',
      },
      animation: {
        'ticker-scroll': 'ticker-scroll 16s linear infinite',
        'border-beam': 'border-beam calc(var(--duration,14)*1s) infinite linear',
        'shimmer-slide': 'shimmer-slide var(--speed,3s) ease-in-out infinite alternate',
        'spin-around': 'spin-around calc(var(--speed,4)*1s) infinite linear',
        'fade-in': 'fade-in 0.5s ease-out',
        'fade-up': 'fade-up 0.5s ease-out',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'gradient-shift': 'gradient-shift 6s ease infinite',
        'shimmer': 'shimmer 1.8s infinite linear',
      },
      keyframes: {
        'ticker-scroll': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        'border-beam': {
          '100%': { 'offset-distance': '100%' },
        },
        'shimmer-slide': {
          to: { transform: 'translate(calc(100cqw - 100%), 0)' },
        },
        'spin-around': {
          '0%': { transform: 'translateZ(0) rotate(0)' },
          '15%, 35%': { transform: 'translateZ(0) rotate(90deg)' },
          '65%, 85%': { transform: 'translateZ(0) rotate(270deg)' },
          '100%': { transform: 'translateZ(0) rotate(360deg)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(6,182,212,0.3)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 40px rgba(6,182,212,0.6)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(6,182,212,0.25)',
        'glow-fuchsia': '0 0 20px rgba(192,38,211,0.25)',
        'glow-sm': '0 0 10px rgba(6,182,212,0.15)',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.06)',
        'card': '0 1px 3px rgba(0,0,0,0.4), 0 8px 32px rgba(0,0,0,0.3)',
        'card-hover': '0 1px 3px rgba(0,0,0,0.5), 0 16px 48px rgba(0,0,0,0.4)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
}
