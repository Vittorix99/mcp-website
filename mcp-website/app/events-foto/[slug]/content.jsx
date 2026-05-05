"use client"

import { useState, useEffect, useMemo, useRef } from "react"
import Link from "next/link"
import NextImage from "next/image"
import { MasonryGallery } from "@/components/pages/pictures/MasonGallery"
import ImageModal from "@/components/pages/modals/ImageModal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

function formatDate(dateString) {
  try {
    const [day, month, year] = (dateString || "").split("-").map(Number)
    return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.${year}`
  } catch {
    return dateString || ""
  }
}

function NavButton({ href, label, disabled }) {
  if (disabled) {
    return (
      <span style={{
        padding: "8px 16px",
        border: "1px solid rgba(245,243,239,0.08)",
        fontFamily: HN, fontSize: "9px",
        letterSpacing: "0.22em", textTransform: "uppercase",
        color: "rgba(245,243,239,0.2)", cursor: "default",
      }}>{label}</span>
    )
  }
  return (
    <Link href={href} prefetch={false} style={{
      padding: "8px 16px",
      border: "1px solid rgba(245,243,239,0.18)",
      fontFamily: HN, fontSize: "9px",
      letterSpacing: "0.22em", textTransform: "uppercase",
      color: "rgba(245,243,239,0.55)", textDecoration: "none",
      transition: "border-color 0.2s, color 0.2s",
    }}>{label}</Link>
  )
}

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
  const [isHydrated, setIsHydrated] = useState(false)
  const images = useMemo(() => pageImages || [], [pageImages])
  const prefetchedRef = useRef(new Set())
  const loadedUrlsRef = useRef(new Set())

  useEffect(() => {
    setIsHydrated(true)
  }, [])

  useEffect(() => {
    loadedUrlsRef.current = new Set()
  }, [images.length, currentPage])

  useEffect(() => {
    if (!Array.isArray(prefetchUrls) || prefetchUrls.length === 0) return
    prefetchUrls.forEach((url) => {
      if (!url || prefetchedRef.current.has(url)) return
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

  if (!event) {
    return (
      <div style={{ minHeight: "100svh", background: "#080808", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>Event not found.</p>
      </div>
    )
  }

  const totalPages = Math.max(1, Math.ceil((totalLength || 0) / pageSize))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages
  const basePath = slug ? `/events-foto/${slug}` : ""
  const pageHref = (page) => (page <= 1 ? basePath : `${basePath}?page=${page}`)
  const hasPhotos = totalLength > 0 || images.length > 0

  return (
    <div style={{ minHeight: "100svh", background: "#080808", paddingTop: "100px" }}>
      {/* Header */}
      <div style={{ padding: "40px 40px 48px" }}>
        <Link href="/events-foto" style={{
          fontFamily: HN, fontSize: "9px", letterSpacing: "0.32em",
          textTransform: "uppercase", color: "rgba(245,243,239,0.35)",
          textDecoration: "none", display: "block", marginBottom: "28px",
        }}>← All Events</Link>
        {event.date && (
          <p style={{
            fontFamily: CH, fontSize: "13px", fontStyle: "italic",
            color: "rgba(245,243,239,0.4)", marginBottom: "8px",
          }}>{formatDate(event.date)}</p>
        )}
        <h1 style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(36px,7vw,90px)", letterSpacing: "-0.04em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.84,
          marginBottom: "8px",
        }}>{event.title || "Event Photos"}</h1>
        <p style={{
          fontFamily: HN, fontSize: "9px",
          letterSpacing: "0.3em", textTransform: "uppercase",
          color: "rgba(245,243,239,0.28)",
        }}>
          {totalLength > 0 ? `${totalLength} photos` : images.length > 0 ? `${images.length} photos` : ""}
          {totalPages > 1 ? ` · Page ${currentPage} / ${totalPages}` : ""}
        </p>
      </div>

      {!hasPhotos ? (
        <div style={{ padding: "0 40px 80px" }}>
          <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
            No photos available.
          </p>
        </div>
      ) : (
        <>
          {/* Pagination top */}
          {totalPages > 1 && (
            <div style={{ padding: "0 40px 32px", display: "flex", gap: "8px", alignItems: "center" }}>
              {canPrev && <NavButton href={pageHref(1)} label="«" />}
              {canPrev && <NavButton href={pageHref(currentPage - 1)} label="‹ Prev" />}
              {canNext && <NavButton href={pageHref(currentPage + 1)} label="Next ›" />}
              {canNext && <NavButton href={pageHref(totalPages)} label="»" />}
            </div>
          )}

          {!isHydrated ? (
            <PhotoGridSkeleton count={Math.min(pageSize, images.length || pageSize)} />
          ) : (
            <>
              {/* Mobile grid */}
              <div className="lg:hidden" style={{ padding: "0 40px 80px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px" }}>
                  {images.map((image, index) => (
                    <MobileImage
                      key={image?.id || image?.src || `img-${index}`}
                      image={image}
                      loadedUrlsRef={loadedUrlsRef}
                      onOpen={() => downloadImage(image)}
                    />
                  ))}
                </div>
              </div>

              {/* Desktop masonry */}
              <div className="hidden lg:block" style={{ padding: "0 56px 80px" }}>
                <MasonryGallery images={images} onImageClick={(src) => setSelectedImage({ src })} />
              </div>
            </>
          )}

          {/* Pagination bottom */}
          {totalPages > 1 && (
            <div style={{ padding: "0 40px 80px", display: "flex", gap: "8px", alignItems: "center", justifyContent: "center" }}>
              {canPrev && <NavButton href={pageHref(currentPage - 1)} label="‹ Previous" />}
              <span style={{ fontFamily: HN, fontSize: "9px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(245,243,239,0.35)", padding: "0 16px" }}>
                {currentPage} / {totalPages}
              </span>
              {canNext && <NavButton href={pageHref(currentPage + 1)} label="Next ›" />}
            </div>
          )}
        </>
      )}

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

function PhotoGridSkeleton({ count = 16 }) {
  const items = Array.from({ length: Math.max(1, count) })
  return (
    <>
      <div className="lg:hidden" style={{ padding: "0 40px 80px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px" }}>
          {items.map((_, index) => (
            <div key={index} style={{ aspectRatio: "1", background: "#111" }} />
          ))}
        </div>
      </div>
      <div className="hidden lg:block" style={{ padding: "0 56px 80px" }}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-2">
          {items.map((_, index) => (
            <div key={index} style={{ aspectRatio: "1", background: "#111" }} />
          ))}
        </div>
      </div>
    </>
  )
}

function MobileImage({ image, loadedUrlsRef, onOpen }) {
  const src = image?.src || "/placeholder.svg"
  const [loaded, setLoaded] = useState(() => loadedUrlsRef?.current?.has(src))
  return (
    <div style={{ position: "relative", overflow: "hidden", aspectRatio: "1" }}>
      {!loaded && <div style={{ position: "absolute", inset: 0, background: "#111" }} />}
      <button
        type="button"
        onClick={onOpen}
        style={{ position: "absolute", inset: 0, zIndex: 10 }}
        aria-label="Open image"
      />
      <NextImage
        src={src}
        alt={image?.alt || ""}
        fill
        sizes="50vw"
        suppressHydrationWarning
        style={{ objectFit: "cover", opacity: loaded ? 1 : 0 }}
        loading="lazy"
        unoptimized
        onLoad={() => { loadedUrlsRef?.current?.add(src); setLoaded(true) }}
        onError={() => { loadedUrlsRef?.current?.add(src); setLoaded(true) }}
      />
    </div>
  )
}
