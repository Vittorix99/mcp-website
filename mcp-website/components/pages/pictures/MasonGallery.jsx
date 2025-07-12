"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Download, Loader2 } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"

export function MasonryGallery({ images }) {
  const [selectedImage, setSelectedImage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [visibleImages, setVisibleImages] = useState([])
  const [currentIndex, setCurrentIndex] = useState(12)

  useEffect(() => {
    if (images?.length > 0) {
      setVisibleImages(images.slice(0, 12))
      setLoading(false)
    }
  }, [images])

  const loadMore = () => {
    const newImages = images.slice(currentIndex, currentIndex + 12)
    setVisibleImages([...visibleImages, ...newImages])
    setCurrentIndex(currentIndex + 12)
  }

  if (loading) {
    return (
      <div className="min-h-[200px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  return (
    <>
      {/* Masonry Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-1">
        {visibleImages.map((image, index) => (
          <motion.div
            key={index}
            className="relative cursor-pointer overflow-hidden"
            style={{ aspectRatio: "1" }}
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
            onClick={() => setSelectedImage(image)}
          >
            <Image src={image?.src || "/placeholder.svg"} alt={image?.alt || ""} fill className="object-cover" />
          </motion.div>
        ))}
      </div>

      {/* Load More Button */}
      {currentIndex < images.length && (
        <div className="mt-8 flex justify-center">
          <Button onClick={loadMore} className="bg-mcp-orange hover:bg-mcp-orange/80 text-black">
            Load More
          </Button>
        </div>
      )}

      {/* Image Preview Modal */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedImage(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative max-w-7xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <Image
                src={selectedImage.src || "/placeholder.svg"}
                alt={selectedImage.alt || ""}
                width={1920}
                height={1080}
                className="w-full h-auto"
              />
              <button
                onClick={() => setSelectedImage(null)}
                className="absolute top-4 right-4 text-white hover:text-mcp-orange transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
              <button
                onClick={() => {
                  const link = document.createElement("a")
                  link.href = selectedImage.src
                  link.download = selectedImage.alt || "image.jpg"
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                }}
                className="absolute bottom-4 right-4 text-white hover:text-mcp-orange transition-colors flex items-center gap-2"
              >
                <Download className="w-6 h-6" />
                <span>Download</span>
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

