"use client"

import { useState, useEffect, useRef } from "react"
import { AnimatePresence } from "framer-motion"
import { getEventById } from "@/services/events"
import { getImageUrls } from "@/config/firebaseStorage"
import { Loader2 } from "lucide-react"
import ImageModal from "@/components/pages/modals/ImageModal"
import { MasonryGallery } from "@/components/pages/pictures/MasonGallery"
import { SectionTitle } from "@/components/ui/section-title"

const CACHE_KEY_PREFIX = "event-photos-cache-v1"
const CACHE_TTL_MS = 1000 * 60 * 60 * 6 // 6 ore

export function EventContent({ id, initialEvent = null }) {
  const [event, setEvent] = useState(initialEvent)
  const [loading, setLoading] = useState(!initialEvent)
  const [error, setError] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imageUrls, setImageUrls] = useState([])
  const [imagesLoading, setImagesLoading] = useState(true) // skeleton per immagini
  const firstImageLoadedRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    const cacheKey = `${CACHE_KEY_PREFIX}:${id}`

    const readCache = () => {
      if (typeof window === "undefined") return null
      try {
        const raw = sessionStorage.getItem(cacheKey)
        if (!raw) return null
        const parsed = JSON.parse(raw)
        if (!parsed?.ts || Date.now() - parsed.ts > CACHE_TTL_MS) {
          sessionStorage.removeItem(cacheKey)
          return null
        }
        return parsed
      } catch {
        sessionStorage.removeItem(cacheKey)
        return null
      }
    }

    const cachedData = readCache()
    const hasCache = Boolean(cachedData)

    if (hasCache) {
      setEvent(cachedData.event || initialEvent || null)
      setImageUrls(cachedData.imageUrls || [])
    } else if (initialEvent) {
      setEvent(initialEvent)
    }

    setLoading(!hasCache && !initialEvent)
    setImagesLoading(!hasCache)
    firstImageLoadedRef.current = !!hasCache
    setError(null)

    async function fetchEventAndPhotos() {
      try {
        const eventResponse = await getEventById(id)
        if (!eventResponse?.success || !eventResponse?.event) {
          if (!initialEvent) setError("Unable to retrieve event details.")
          setImagesLoading(false)
          if (!initialEvent) setLoading(false)
          return
        }

        if (cancelled) return
        const cacheableEvent = cachedData?.event || initialEvent || eventResponse.event
        const freshEvent = cacheableEvent || eventResponse.event

        if (!freshEvent) {
          setError("Unable to retrieve event details.")
          setLoading(false)
          setImagesLoading(false)
          return
        }

        setEvent(freshEvent)
        setLoading(false)

        let formattedImageUrls = []
        if (freshEvent.photoPath) {
          const photoUrls = await getImageUrls(`foto/${freshEvent.photoPath}`)
          if (cancelled) return

          formattedImageUrls = (photoUrls || [])
            .filter((url) => !url.toLowerCase().includes("cover.jpg"))
            .map((url, index) => ({
              src: url,
              alt: `${freshEvent.title} - Photo ${index + 1}`,
            }))
          setImageUrls(formattedImageUrls)

          if (formattedImageUrls.length > 0) {
            const fallback = setTimeout(() => {
              if (!cancelled && !firstImageLoadedRef.current) {
                setImagesLoading(false)
              }
            }, 1500)

            const img = new Image()
            img.onload = () => {
              firstImageLoadedRef.current = true
              clearTimeout(fallback)
              if (!cancelled) setImagesLoading(false)
            }
            img.onerror = () => {
              clearTimeout(fallback)
              if (!cancelled) setImagesLoading(false)
            }
            img.src = formattedImageUrls[0]?.src
          } else {
            setImagesLoading(false)
          }
        } else {
          setImageUrls([])
          setImagesLoading(false)
        }

        if (!cancelled && typeof window !== "undefined") {
          sessionStorage.setItem(
            cacheKey,
            JSON.stringify({
              event: freshEvent,
              imageUrls: formattedImageUrls,
              ts: Date.now(),
            })
          )
        }
      } catch (err) {
        if (!cancelled) {
          setError("An error occurred while fetching event data.")
          setLoading(false)
          setImagesLoading(false)
        }
      }
    }

    fetchEventAndPhotos()
    return () => {
      cancelled = true
    }
  }, [id, initialEvent])

  // Wrapper a prova di overflow su mobile (navbar/pagine che strabordano)
  const MobileSafe = ({ children }) => (
    <div className="w-full overflow-x-hidden sm:overflow-x-visible">{children}</div>
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4">
          <div className="text-center text-mcp-orange text-xl">{error || "Event not found"}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-black py-24">
      <MobileSafe>
        <div className="container mx-auto px-4">
          <SectionTitle as="h1" className="mt-8">
            Event Photos
          </SectionTitle>

          {/* Skeleton immagini finché non è pronta almeno la prima */}
          {imagesLoading ? (
            <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="aspect-[3/4] w-full rounded bg-zinc-900 animate-pulse"
                  aria-hidden="true"
                />
              ))}
            </div>
          ) : (
            <MasonryGallery images={imageUrls} onImageClick={(src) => setSelectedImage(src)} />
          )}
        </div>
      </MobileSafe>

      <AnimatePresence>
        {selectedImage && (
          <ImageModal
            imageUrl={selectedImage}
            onClose={() => setSelectedImage(null)}
            onDownload={() => {
              const link = document.createElement("a")
              link.href = selectedImage
              link.download = `${event.title}_photo.jpg`
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
