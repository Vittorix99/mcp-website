"use client"

import { useState, useEffect, useMemo, useRef, useCallback, memo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Download } from "lucide-react"
import Image from "next/image"

async function safeDownload(src, filename = "image.jpg") {
  try {
    const res = await fetch(src, { cache: "no-store" })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.rel = "noopener"
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1500)
  } catch (e) {
    const a = document.createElement("a")
    a.href = src
    a.target = "_blank"
    a.rel = "noopener"
    document.body.appendChild(a)
    a.click()
    a.remove()
  }
}

export const MasonryGallery = memo(function MasonryGallery({
  images = [],
  onAllLoaded,
  onImageClick,
  onProgress,
}) {
  const [selectedImage, setSelectedImage] = useState(null)
  const [loadedMap, setLoadedMap] = useState({})
  const scrollYRef = useRef(0)
  const progressRef = useRef(onProgress)
  const allLoadedRef = useRef(onAllLoaded)
  const lastProgressRef = useRef(-1)
  const allLoadedSentRef = useRef(false)

  const visibleKeys = useMemo(() => {
    return images.map((image, index) => image?.id || image?.src || `img-${index}`)
  }, [images])

  const markLoaded = useCallback((key) => {
    setLoadedMap((prev) => (prev[key] ? prev : { ...prev, [key]: true }))
  }, [])

  useEffect(() => {
    progressRef.current = onProgress
  }, [onProgress])

  useEffect(() => {
    allLoadedRef.current = onAllLoaded
  }, [onAllLoaded])

  useEffect(() => {
    setLoadedMap({})
    lastProgressRef.current = -1
    allLoadedSentRef.current = false
  }, [visibleKeys.join("|")])

  useEffect(() => {
    const total = visibleKeys.length
    const defer = (fn) => {
      if (typeof window === "undefined") return
      if (typeof requestAnimationFrame === "function") {
        requestAnimationFrame(fn)
      } else {
        setTimeout(fn, 0)
      }
    }

    if (total === 0) {
      if (typeof progressRef.current === "function") defer(() => progressRef.current(1))
      if (typeof allLoadedRef.current === "function") defer(() => allLoadedRef.current())
      return
    }

    const loadedCount = visibleKeys.filter((key) => loadedMap[key]).length
    const ratio = loadedCount / total
    if (ratio !== lastProgressRef.current) {
      lastProgressRef.current = ratio
      if (typeof progressRef.current === "function") defer(() => progressRef.current(ratio))
    }
    if (loadedCount === total && !allLoadedSentRef.current) {
      allLoadedSentRef.current = true
      if (typeof allLoadedRef.current === "function") defer(() => allLoadedRef.current())
    }
  }, [loadedMap, visibleKeys])

  const onOpenModal = useCallback((img) => {
    scrollYRef.current = window.scrollY
    document.body.style.top = `-${scrollYRef.current}px`
    document.body.style.position = "fixed"
    setSelectedImage(img)
  }, [])

  const onCloseModal = useCallback(() => {
    setSelectedImage(null)
    document.body.style.position = ""
    document.body.style.top = ""
    window.scrollTo({ top: scrollYRef.current, behavior: "instant" })
  }, [])

  const handleImageClick = (image) => {
    if (typeof onImageClick === "function") {
      onImageClick(image?.src)
      return
    }
    onOpenModal(image)
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-2">
        {images.map((image, index) => {
          const key = image?.id || image?.src || `img-${index}`
          const isLoaded = loadedMap[key]
          return (
            <motion.div
              key={key}
              className="relative cursor-pointer overflow-hidden"
              style={{ aspectRatio: "1" }}
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
              onClick={() => handleImageClick(image)}
            >
              {!isLoaded && <div className="absolute inset-0 bg-zinc-900 animate-pulse" />}
              <Image
                src={image?.src || "/placeholder.svg"}
                alt={image?.alt || ""}
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, (max-width: 1536px) 33vw, 25vw"
                suppressHydrationWarning
                className={`object-cover ${isLoaded ? "opacity-100" : "opacity-0"}`}
                loading="eager"
                unoptimized
                onLoad={() => markLoaded(key)}
                onError={() => markLoaded(key)}
              />
            </motion.div>
          )
        })}
      </div>

      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[9999] bg-black/90"
            style={{ paddingTop: "env(safe-area-inset-top)" }}
          >
            <div className="absolute inset-0" onClick={onCloseModal} />

            <div
              className="relative flex items-center justify-between px-3 py-3 sm:px-4 sm:py-4 pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={onCloseModal}
                className="text-white hover:text-mcp-orange transition-colors"
                aria-label="Chiudi anteprima"
              >
                <X className="w-6 h-6" />
              </button>

              <button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  safeDownload(selectedImage.src, selectedImage.alt || "image.jpg")
                }}
                className="text-white hover:text-mcp-orange transition-colors flex items-center gap-2"
                aria-label="Scarica immagine"
              >
                <Download className="w-5 h-5" />
                <span className="hidden sm:inline">Download</span>
              </button>
            </div>

            <div
              className="relative w-screen h-[calc(100vh-56px)] sm:h-[calc(100vh-72px)] overflow-hidden touch-pan-y overscroll-contain pointer-events-auto"
              onClick={onCloseModal}
            >
              <div className="relative mx-auto h-full w-full sm:max-w-7xl" onClick={(e) => e.stopPropagation()}>
                <Image
                  src={selectedImage.src || "/placeholder.svg"}
                  alt={selectedImage.alt || ""}
                  fill
                  sizes="100vw"
                  suppressHydrationWarning
                  className="object-contain"
                  priority
                  unoptimized
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
})

MasonryGallery.displayName = "MasonryGallery"
