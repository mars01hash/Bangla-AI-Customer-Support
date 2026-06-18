/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0F172A",      // Dark Slate primary background
        darkCard: "#1E293B",    // Slate card background
        accentGreen: "#10B981", // Emerald accent
        accentPurple: "#8B5CF6",// Violet accent
        accentPink: "#EC4899"   // Pink indicator
      },
      fontFamily: {
        outfit: ["Outfit", "sans-serif"],
      }
    },
  },
  plugins: [],
}
