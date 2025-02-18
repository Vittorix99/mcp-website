"use client"

import { motion } from "framer-motion"
import { X, Download, ZoomIn } from "lucide-react"
import { useState, useEffect } from "react"
import Image from "next/image"

const ImageModal = ({ imageUrl, onClose, onDownload }) => {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [isFullSize, setIsFullSize] = useState(false)

  useEffect(() => {
    const img = new Image()
    img.onload = () => setImageLoaded(true)
    img.src = imageUrl
  }, [imageUrl])

  const toggleFullSize = () => {
    setIsFullSize(!isFullSize)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0.8 }}
        className="relative w-full h-full max-w-2xl max-h-[70vh] p-4 flex flex-col justify-center items-center"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative w-full h-full flex justify-center items-center overflow-hidden bg-black bg-opacity-50 rounded-lg p-2">
          {imageLoaded ? (
            <Image
              src={imageUrl || "/placeholder.svg"}
              alt="Event photo"
              layout="fill"
              objectFit="contain"
              quality={isFullSize ? 100 : 75}
            />
          ) : (
            <div className="w-16 h-16 border-4 border-mcp-orange border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-white hover:text-mcp-orange transition-colors bg-black bg-opacity-50 rounded-full p-2"
        >
          <X size={24} />
        </button>
        <button
          onClick={toggleFullSize}
          className="absolute top-2 left-2 text-white hover:text-mcp-orange transition-colors bg-black bg-opacity-50 rounded-full p-2"
        >
          <ZoomIn size={24} />
        </button>
        <button
          onClick={onDownload}
          className="absolute bottom-2 right-2 text-white hover:text-mcp-orange transition-colors bg-black bg-opacity-50 rounded-full p-2 flex items-center"
        >
          <Download size={24} className="mr-2" />
          <span className="hidden sm:inline">Download Original</span>
        </button>
      </motion.div>
    </motion.div>
  )
}

export default ImageModal

