"use client"

import Image from "next/image"
import { motion } from "framer-motion"
import { useEffect, useState } from "react"

export function AnimatedSectionDivider({ color = "ORANGE", className = "", width = 200, height = 80 }) {
  // Verifica che il colore sia valido
  const validColors = ["BLACK", "ORANGE", "RED", "WHITE"]
  const patternColor = validColors.includes(color.toUpperCase()) ? color.toUpperCase() : "ORANGE"

  // Stato per tenere traccia della larghezza dello schermo
  const [isMobile, setIsMobile] = useState(false)

  // Calcola dimensioni ridotte per mobile
  const mobileWidth = Math.floor(width * 0.7)
  const mobileHeight = Math.floor(height * 0.7)

  // Effetto per rilevare la dimensione dello schermo
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }

    // Controlla all'inizio
    checkIfMobile()

    // Aggiungi event listener per il resize
    window.addEventListener("resize", checkIfMobile)

    // Cleanup
    return () => window.removeEventListener("resize", checkIfMobile)
  }, [])

  // Dimensioni responsive basate sulla dimensione dello schermo
  const responsiveWidth = isMobile ? mobileWidth : width
  const responsiveHeight = isMobile ? mobileHeight : height

  return (
    <div className={`w-full flex justify-center py-1 md:py-3 ${className}`}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true, margin: "-100px" }}
      >
        {/* Singolo elemento Image con dimensioni responsive */}
        <Image
          src={`/patterns/MCP PATTERN - ${patternColor}.png`}
          alt={`Wave Pattern ${patternColor}`}
          width={responsiveWidth}
          height={responsiveHeight}
          className="opacity-80"
          priority={true}
        />
      </motion.div>
    </div>
  )
}

