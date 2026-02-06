"use client"

import { useState, useEffect, useMemo, useRef } from "react"
import Link from "next/link"
import { MasonryGallery } from "@/components/pages/pictures/MasonGallery"
import { PageHeader } from "@/components/PageHeader"
import { Button } from "@/components/ui/button"
import NextImage from "next/image"
import ImageModal from "@/components/pages/modals/ImageModal"

export function EventContent({
  initialEvent = null,
  pageImages = [],
  pageSize = 16,
  totalLength = 0,
  currentPage = 1,
  slug,
  prefetchUrls = [],
}) {
  const [event] = useState(initialEvent)
  const [selectedImage, setSelectedImage] = useState(null)
  const images = useMemo(() => pageImages || [], [pageImages])
  const prefetchedRef = useRef(new Set())
  const loadedUrlsRef = useRef(new Set())

  useEffect(() => {
    // Reset mobile cache only when page changes
    loadedUrlsRef.current = new Set()
  }, [images.length, currentPage])


  useEffect(() => {
    if (!Array.isArray(prefetchUrls) || prefetchUrls.length === 0) return
    prefetchUrls.forEach((url) => {
      if (!url) return
      if (prefetchedRef.current.has(url)) return
      prefetchedRef.current.add(url)
      if (typeof window === "undefined") return
      const img = new window.Image()
      img.src = url
    })
  }, [prefetchUrls])

  const downloadImage = (image) => {
    const src = image?.fullSrc || image?.src
    if (!src) return
    const link = document.createElement("a")
    link.href = src
    link.download = `${event?.title || "event"}_photo.jpg`
    link.rel = "noopener"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Wrapper a prova di overflow su mobile (navbar/pagine che strabordano)
  const MobileSafe = ({ children }) => (
    <div className="w-full overflow-x-hidden sm:overflow-x-visible">{children}</div>
  )

  if (!event) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4">
          <div className="text-center text-mcp-orange text-xl">Event not found</div>
        </div>
      </div>
    )
  }

  const totalPages = Math.max(1, Math.ceil((totalLength || 0) / pageSize))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages
  const canLast = currentPage < totalPages
  const basePath = slug ? `/events-foto/${slug}` : ""
  const pageHref = (page) => (page <= 1 ? basePath : `${basePath}?page=${page}`)
  const hasPhotos = totalLength > 0 || images.length > 0
  const remaining = totalLength
    ? Math.max(0, totalLength - (currentPage - 1) * pageSize)
    : pageSize
  const skeletonCount = Math.max(1, Math.min(pageSize, remaining || pageSize))

  return (
    <div className="bg-black py-8">
      <MobileSafe>
        <div className="container mx-auto px-4">
          <PageHeader title="Event Photos" />

          {!hasPhotos ? (
            <div className="mt-6 mx-2 text-center text-gray-400">No photos available.</div>
          ) : (
            <>
              <div className="flex items-center justify-center gap-4 sm:gap-6 mt-4 mb-4 text-center">
                <div className="hidden sm:block text-sm text-gray-400">
                  Mostrando <span className="text-white">{images.length}</span> su {totalLength}
                </div>
                <div className="flex items-center gap-1 sm:gap-2 flex-nowrap text-xs sm:text-sm">
                  {canPrev ? (
                    <Button variant="outline" size="sm"  asChild>
                      <Link href={pageHref(1)} prefetch={false}>
                        <span className="sm:hidden">«</span>
                        <span className="hidden sm:inline">« Inizio</span>
                      </Link>
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" disabled>
                      <span className="sm:hidden">«</span>
                      <span className="hidden sm:inline">« Inizio</span>
                    </Button>
                  )}
                  {canPrev ? (
                    <Button variant="outline" size="sm" className="ml-2" asChild>
                      <Link href={pageHref(currentPage - 1)} prefetch={false}>
                        <span className="sm:hidden">‹</span>
                        <span className="hidden sm:inline">‹ Precedente</span>
                      </Link>
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" className="ml-2" disabled>
                      <span className="sm:hidden">‹</span>
                      <span className="hidden sm:inline">‹ Precedente</span>
                    </Button>
                  )}
                  <span className="text-gray-300 whitespace-nowrap mx-6">
                    <span className="hidden sm:inline">Pagina </span>
                    <span className="text-white">{currentPage}</span>
                    <span className="hidden sm:inline"> / </span>
                    <span className="sm:hidden">/</span>
                    {totalPages}
                  </span>
                  {canNext ? (
                    <Button variant="outline" size="sm" className="mr-2" asChild>
                      <Link href={pageHref(currentPage + 1)} prefetch={false}>
                        <span className="sm:hidden">›</span>
                        <span className="hidden sm:inline">Successiva ›</span>
                      </Link>
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" className="" disabled>
                      <span className="sm:hidden">›</span>
                      <span className="hidden sm:inline">Successiva ›</span>
                    </Button>
                  )}
                  {canLast ? (
                    <Button variant="outline" size="sm" asChild>
                      <Link href={pageHref(totalPages)} prefetch={false}>
                        <span className="sm:hidden">»</span>
                        <span className="hidden sm:inline">Fine »</span>
                      </Link>
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" className="gap-4" disabled>
                      <span className="sm:hidden">»</span>
                      <span className="hidden sm:inline">Fine »</span>
                    </Button>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-1 lg:hidden" suppressHydrationWarning>
                {images.map((image, index) => (
                  <MobileImage
                    key={image?.id || image?.src || `img-${index}`}
                    image={image}
                    loadedUrlsRef={loadedUrlsRef}
                    onOpen={() => downloadImage(image)}
                  />
                ))}
              </div>
              <div className="hidden lg:block" suppressHydrationWarning>
                <MasonryGallery images={images} onImageClick={(src) => setSelectedImage({ src })} />
              </div>

              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-center gap-4 sm:gap-6 text-center">
                  <div className="text-sm text-gray-400">
                    Pagina <span className="text-white">{currentPage}</span> di {totalPages}
                  </div>
                  <div className="flex items-center gap-2">
                    {canPrev ? (
                      <Button variant="outline" size="sm" asChild>
                        <Link href={pageHref(currentPage - 1)} prefetch={false}>
                          ‹ Precedente
                        </Link>
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm" disabled>
                        ‹ Precedente
                      </Button>
                    )}
                    {canNext ? (
                      <Button variant="outline" size="sm" asChild>
                        <Link href={pageHref(currentPage + 1)} prefetch={false}>
                          Successiva ›
                        </Link>
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm" disabled>
                        Successiva ›
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </MobileSafe>
      {selectedImage && (
        <ImageModal
          imageUrl={selectedImage?.src}
          onClose={() => setSelectedImage(null)}
          onDownload={() => {
            const link = document.createElement("a")
            link.href = selectedImage?.fullSrc || selectedImage?.src
            link.download = `${event?.title || "event"}_photo.jpg`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
          }}
        />
      )}
    </div>
  )
}

function MobileImage({ image, loadedUrlsRef, onOpen }) {
  const src = image?.src || "/placeholder.svg"
  const [loaded, setLoaded] = useState(() => loadedUrlsRef?.current?.has(src))
  return (
    <div className="relative overflow-hidden" style={{ aspectRatio: "1" }}>
      {!loaded && <div className="absolute inset-0 bg-zinc-900" />}
      <button
        type="button"
        onClick={onOpen}
        className="absolute inset-0 z-10"
        aria-label="Apri immagine"
      />
      <NextImage
        src={src}
        alt={image?.alt || ""}
        fill
        sizes="50vw"
        className={loaded ? "object-cover opacity-100" : "object-cover opacity-0"}
        loading="lazy"
        unoptimized
        onLoad={() => {
          loadedUrlsRef?.current?.add(src)
          setLoaded(true)
        }}
        onError={() => {
          loadedUrlsRef?.current?.add(src)
          setLoaded(true)
        }}
      />
    </div>
  )
}
