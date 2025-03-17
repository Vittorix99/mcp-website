/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ["class"],
	content: [
	  "./pages/**/*.{js,jsx,mdx}",
	  "./components/**/*.{js,jsx,mdx}",
	  "./app/**/*.{js,jsx,mdx}",
	  "*.{js,jsx,mdx}",
	  "*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
	  container: {
		center: true,
		padding: "2rem",
		screens: {
		  "2xl": "1400px",
		},
	  },
	  extend: {
		fontFamily: {
		  charter: ["var(--font-charter)", "serif"],
		  helvetica: ["var(--font-helvetica)", "sans-serif"],
		  atlantico: ["var(--font-atlantico)", "sans-serif"],
		  // Override default font families
		  sans: ["var(--font-helvetica)", "ui-sans-serif", "system-ui", "sans-serif"],
		  serif: ["var(--font-charter)", "ui-serif", "Georgia", "serif"],
		},
		colors: {
		  border: "hsl(var(--border))",
		  input: "hsl(var(--input))",
		  ring: "hsl(var(--ring))",
		  background: "hsl(var(--background))",
		  foreground: "hsl(var(--foreground))",
		  primary: {
			DEFAULT: "hsl(var(--primary))",
			foreground: "hsl(var(--primary-foreground))",
		  },
		  secondary: {
			DEFAULT: "hsl(var(--secondary))",
			foreground: "hsl(var(--secondary-foreground))",
		  },
		  destructive: {
			DEFAULT: "hsl(var(--destructive))",
			foreground: "hsl(var(--destructive-foreground))",
		  },
		  muted: {
			DEFAULT: "hsl(var(--muted))",
			foreground: "hsl(var(--muted-foreground))",
		  },
		  accent: {
			DEFAULT: "hsl(var(--accent))",
			foreground: "hsl(var(--accent-foreground))",
		  },
		  popover: {
			DEFAULT: "hsl(var(--popover))",
			foreground: "hsl(var(--popover-foreground))",
		  },
		  card: {
			DEFAULT: "hsl(var(--card))",
			foreground: "hsl(var(--card-foreground))",
		  },
		  mcp: {
			orange: "#FF6B00",
			red: "#FF0000",
			black: "#000000",
		  },
		},
		borderRadius: {
		  lg: "var(--radius)",
		  md: "calc(var(--radius) - 2px)",
		  sm: "calc(var(--radius) - 4px)",
		},
		backgroundImage: {
		  "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
		  "mcp-gradient": "linear-gradient(90deg, #FF6B00 0%, #FF0000 100%)",
		  "neon-gradient": "linear-gradient(90deg, #9EFF00 0%, #00F0FF 100%)",
		},
		keyframes: {
		  wave: {
			"0%, 100%": { transform: "translateY(0)" },
			"50%": { transform: "translateY(-5px)" },
		  },
		},
		animation: {
		  wave: "wave 3s ease-in-out infinite",
		},
	  },
	},
	plugins: [require("tailwindcss-animate")],
  }
  
  