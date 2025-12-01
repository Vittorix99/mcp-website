"use client"

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Download, Loader2 } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"

async function safeDownload(src, filename = 'image.jpg') {
  try {
    const res = await fetch(src, { cache: 'no-store' })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.rel = 'noopener'
    // Do NOT set target to avoid opening a new tab; keep history intact
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1500)
  } catch (e) {
    // Fallback: open in new tab without affecting history stack
    const a = document.createElement('a')
    a.href = src
    a.target = '_blank'
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
  }
}

/**
 * MasonryGallery con paginazione reale.
 *
 * Modalità A (client-slice, default):
 *  - passi "images" con TUTTE le immagini e NON passi onPageChange/totalCount
 *  - la galleria esegue slice per pagina (non carica tutto in DOM)
 *
 * Modalità B (server-paging):
 *  - passi "images" contenenti SOLO la pagina corrente
 *  - passi anche "totalCount" (totale globale) e "onPageChange(page, pageSize)" (async)
 *  - la galleria richiama onPageChange quando cambi pagina
 */

export function MasonryGallery({
  images = [],
  pageSize = 24,
  totalCount, // opzionale: richiesto in server-paging
  onPageChange, // opzionale: se presente, abilita server-paging
  initialPage = 1,
}) {
  const serverPaging = typeof onPageChange === "function" && typeof totalCount === "number"

  const [selectedImage, setSelectedImage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(initialPage)
  const [internalTotalPages, setInternalTotalPages] = useState(1)

  // Salviamo/ristoriamo lo scroll per evitare "salti all'inizio"
  const scrollYRef = useRef(0)
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

  // Calcolo pagine totali
  useEffect(() => {
    const total = serverPaging ? (totalCount || 0) : (Array.isArray(images) ? images.length : 0)
    const pages = Math.max(1, Math.ceil(total / pageSize))
    setInternalTotalPages(pages)
    setLoading(false)
    // non resettare la page se rimane valida
    setPage((prev) => Math.min(Math.max(1, prev || 1), pages))
  }, [images, pageSize, totalCount, serverPaging])

  // Se server-paging, chiedi i dati quando cambia pagina
  useEffect(() => {
    if (!serverPaging) return
    let cancelled = false
    const run = async () => {
      setLoading(true)
      try {
        await onPageChange(page, pageSize)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [page, pageSize, serverPaging, onPageChange])

  // In client-slice mostri solo gli elementi di quella pagina
  const visibleImages = useMemo(() => {
    if (serverPaging) return images // già pagina corrente
    const start = (page - 1) * pageSize
    const end = start + pageSize
    return images.slice(start, end)
  }, [images, page, pageSize, serverPaging])

  const canPrev = page > 1
  const canNext = page < internalTotalPages

  const goToPage = (p) => {
    const target = Math.min(Math.max(1, p), internalTotalPages)
    if (target !== page) setPage(target)
  }

  return (
    <>
      {/* Toolbar di paginazione */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-400">
          {serverPaging ? (
            <>
              Mostrando <span className="text-white">{visibleImages.length}</span> su {totalCount || 0}
            </>
          ) : (
            <>
              Mostrando <span className="text-white">{visibleImages.length}</span> di {images.length}
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled={!canPrev || loading} onClick={() => goToPage(1)}>
            « Inizio
          </Button>
          <Button variant="outline" size="sm" disabled={!canPrev || loading} onClick={() => goToPage(page - 1)}>
            ‹ Precedente
          </Button>
          <span className="text-sm text-gray-300">
            Pagina <span className="text-white">{page}</span> / {internalTotalPages}
          </span>
          <Button variant="outline" size="sm" disabled={!canNext || loading} onClick={() => goToPage(page + 1)}>
            Successiva ›
          </Button>
          <Button variant="outline" size="sm" disabled={!canNext || loading} onClick={() => goToPage(internalTotalPages)}>
            Fine »
          </Button>
        </div>
      </div>

      {/* Stato di caricamento pagina (solo server-paging) */}
      {loading && (
        <div className="min-h-[120px] flex items-center justify-center">
          <Loader2 className="w-6 h-6 text-mcp-orange animate-spin" />
        </div>
      )}

      {/* Masonry Grid */}
      {!loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-1">
          {visibleImages.map((image, index) => {
            const key = image?.id || image?.src || `img-${page}-${index}`
            return (
              <motion.div
                key={key}
                className="relative cursor-pointer overflow-hidden"
                style={{ aspectRatio: "1" }}
                whileHover={{ scale: 1.02 }}
                transition={{ duration: 0.2 }}
                onClick={() => onOpenModal(image)}
              >
                <Image
                  src={image?.src || "/placeholder.svg"}
                  alt={image?.alt || ""}
                  fill
                  sizes="(max-width: 1024px) 50vw, 25vw"
                  className="object-cover"
                  loading={serverPaging ? "eager" : "lazy"}
                />
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Footer paginazione */}
      {!loading && internalTotalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Pagina <span className="text-white">{page}</span> di {internalTotalPages}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={!canPrev} onClick={() => goToPage(page - 1)}>
              ‹ Precedente
            </Button>
            <Button variant="outline" size="sm" disabled={!canNext} onClick={() => goToPage(page + 1)}>
              Successiva ›
            </Button>
          </div>
        </div>
      )}

      {/* Image Preview Modal */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[9999] bg-black/90"
            style={{ paddingTop: 'env(safe-area-inset-top)' }}
          >
            {/* Backdrop that absorbs any click (safety) */}
            <div className="absolute inset-0" onClick={onCloseModal} />

            {/* Top bar (safe for mobile notch) */}
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
                  safeDownload(selectedImage.src, selectedImage.alt || 'image.jpg')
                }}
                className="text-white hover:text-mcp-orange transition-colors flex items-center gap-2"
                aria-label="Scarica immagine"
              >
                <Download className="w-5 h-5" />
                <span className="hidden sm:inline">Download</span>
              </button>
            </div>

            {/* Image area */}
            <div
              className="relative w-screen h-[calc(100vh-56px)] sm:h-[calc(100vh-72px)] overflow-hidden touch-pan-y overscroll-contain pointer-events-auto"
              onClick={onCloseModal}
            >
              <div
                className="relative mx-auto h-full w-full sm:max-w-7xl"
                onClick={(e) => e.stopPropagation()}
              >
                <Image
                  src={selectedImage.src || '/placeholder.svg'}
                  alt={selectedImage.alt || ''}
                  fill
                  sizes="100vw"
                  className="object-contain"
                  priority
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
