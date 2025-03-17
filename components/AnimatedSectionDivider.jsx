"use client"

import Image from "next/image"
import { motion } from "framer-motion"

export function AnimatedSectionDivider({ color = "ORANGE", className = "", width = 200, height = 80 }) {
  // Verifica che il colore sia valido
  const validColors = ["BLACK", "ORANGE", "RED", "WHITE"]
  const patternColor = validColors.includes(color.toUpperCase()) ? color.toUpperCase() : "ORANGE"

  return (
    <div className={`w-full flex justify-center  ${className}`}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true, margin: "-100px" }}
      >
        <Image
          src={`/patterns/MCP PATTERN - ${patternColor}.png`}
          alt={`Wave Pattern ${patternColor}`}
          width={width}
          height={height}
          className="opacity-80"
        />
      </motion.div>
    </div>
  )
}

