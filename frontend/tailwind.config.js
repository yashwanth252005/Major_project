/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#d9e5ff",
          400: "#5b8cff",
          500: "#3b6fed",
          600: "#2c56c9",
          900: "#101a3d",
        },
      },
    },
  },
  plugins: [],
};
