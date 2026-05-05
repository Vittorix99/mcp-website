import Image from "next/image"

export function SectionDivider({ color = "ORANGE", className = "", width = 500, height = 80 }) {
  const validColors = ["BLACK", "ORANGE", "RED", "WHITE"]
  const patternColor = validColors.includes(color.toUpperCase()) ? color.toUpperCase() : "ORANGE"

  return (
    <div className={`w-full flex justify-center py-8 ${className}`}>
      <Image
        src={`/patterns/MCP PATTERN - ${patternColor}.png`}
        alt={`Wave Pattern ${patternColor}`}
        width={width}
        height={height}
        className="opacity-80"
      />
    </div>
  )
}

export function WaveDivider({ color = "rgba(224,120,0,0.18)", scale = 1 }) {
  return (
    <div style={{ lineHeight: 0, overflow: "hidden" }}>
      <svg
        viewBox="0 0 1200 60"
        preserveAspectRatio="none"
        style={{ width: "100%", height: `${40 * scale}px`, display: "block" }}
        fill="none"
      >
        <path
          d="M0,30 C80,5 160,55 240,30 C320,5 400,55 480,30 C560,5 640,55 720,30 C800,5 880,55 960,30 C1040,5 1120,55 1200,30"
          stroke={color}
          strokeWidth={`${7 * scale}`}
          strokeLinecap="round"
          fill="none"
        />
      </svg>
    </div>
  )
}

