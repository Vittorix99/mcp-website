import Image from "next/image"

export function SectionDivider({ color = "ORANGE", className = "", width = 500, height = 80 }) {
  // Verifica che il colore sia valido
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

