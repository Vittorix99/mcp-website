"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { motion, AnimatePresence } from "framer-motion"
import { getImageUrls } from "@/config/firebase"

export function AboutUs() {
  const [images, setImages] = useState([])
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  useEffect(() => {
    async function fetchImages() {
      try {
        const allUrls = await getImageUrls("foto/showcase")
        const shuffled = allUrls.sort(() => 0.5 - Math.random())
        setImages(shuffled.slice(0, 20))
      } catch (error) {
        console.error("Error fetching images:", error)
      }
    }
    fetchImages()
  }, [])

  useEffect(() => {
    if (images.length > 0) {
      const interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % images.length)
      }, 8000) // Change image every 8 seconds

      return () => clearInterval(interval)
    }
  }, [images.length])

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  const imageVariants = {
    enter: (direction) => ({
      opacity: 0,
      scale: direction > 0 ? 1.1 : 0.9,
    }),
    center: {
      opacity: 1,
      scale: 1,
      transition: {
        opacity: { duration: 1.5, ease: "easeInOut" },
        scale: { duration: 1.5, ease: "easeInOut" },
      },
    },
    exit: (direction) => ({
      opacity: 0,
      scale: direction < 0 ? 1.1 : 0.9,
      transition: {
        opacity: { duration: 1.5, ease: "easeInOut" },
        scale: { duration: 1.5, ease: "easeInOut" },
      },
    }),
  }

  return (
    <section className="py-12 bg-black overflow-hidden relative">
      <div className="container mx-auto px-4 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center max-w-7xl mx-auto">
          {/* Image Gallery */}
          <div className="relative aspect-square w-full overflow-hidden rounded-lg shadow-lg">
            <AnimatePresence initial={false} custom={currentImageIndex}>
              {images[currentImageIndex] && (
                <motion.div
                  key={currentImageIndex}
                  custom={currentImageIndex}
                  variants={imageVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  className="absolute inset-0"
                >
                  <Image
                    src={images[currentImageIndex] || "/placeholder.svg"}
                    alt="MCP Event"
                    fill
                    className="object-cover"
                    priority
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Content */}
          <div className="space-y-6">
            <motion.h2
              className="font-atlantico text-5xl md:text-5xl font-bold mb-8 gradient-text text-center"
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              variants={fadeInUp}
            >
              Our Philosophy
            </motion.h2>

            <motion.p
              className="font-helvetica text-lg md:text-xl text-gray-300"
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              variants={fadeInUp}
            >
              Music Connecting People was born to find a safe, emotionally immersive, sonorously & visually stunning way
              of partying.
            </motion.p>

            <motion.p
              className="font-helvetica text-lg md:text-xl text-gray-300"
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              variants={fadeInUp}
            >
              We believe that through music, it is possible to reconnect with our inner essence and share it in real
              life. Electronic music offers not only the best journey when celebrating but also a way of
              self-reconciliation and embracing new horizons.
            </motion.p>

            <motion.p
              className="font-charter italic text-lg md:text-xl text-orange-300"
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              variants={fadeInUp}
            >
              "We are drawn toward the future, while finding a guide in the past, lost in the present. Our future
              represents a fully committed goal of innovation and sustainability, the past the underground sounds that
              represent electronic music, and the present the total devotion to feelings, emotions, and connections."
            </motion.p>
          </div>
        </div>
      </div>
      <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-mcp-orange/5 to-black/0 pointer-events-none" />
    </section>
  )
}

