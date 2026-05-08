"use client"

import { useState, useMemo, useCallback, useRef } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
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
}) {
  const [event] = useState(initialEvent)
  const [selectedImage, setSelectedImage] = useState(null)
  const images = useMemo(() => pageImages || [], [pageImages])
  const router = useRouter()
  const prefetchedPagesRef = useRef(new Set())

  const totalPages = Math.max(1, Math.ceil((totalLength || 0) / pageSize))
  const canPrev = currentPage > 1
  const canNext = currentPage < totalPages
  const basePath = slug ? `/events-foto/${slug}` : ""
  const pageHref = useCallback((page) => (page <= 1 ? basePath : `${basePath}?page=${page}`), [basePath])

  const prefetchNextPage = useCallback(() => {
    if (!canNext || !slug || typeof window === "undefined") return

    const nextPage = currentPage + 1
    const key = `${basePath || event?.slug || "event"}:${nextPage}`
    if (prefetchedPagesRef.current.has(key)) return
    prefetchedPagesRef.current.add(key)

    const nextHref = pageHref(nextPage)
    router.prefetch(nextHref)

    const preloadNextImages = async () => {
      try {
        const response = await fetch(`/api/event-photos/${encodeURIComponent(slug)}?page=${nextPage}&pageSize=${pageSize}`, {
          cache: "force-cache",
        })
        if (!response.ok) return

        const { pageUrls = [] } = await response.json()
        pageUrls.forEach((url) => {
          if (!url) return
          const img = new window.Image()
          img.decoding = "async"
          img.src = url
        })
      } catch {
        // Best-effort prefetch only; navigation still works without it.
      }
    }

    if (typeof window.requestIdleCallback === "function") {
      window.requestIdleCallback(() => { preloadNextImages() }, { timeout: 2000 })
    } else {
      window.setTimeout(preloadNextImages, 500)
    }
  }, [basePath, canNext, currentPage, event?.slug, pageHref, pageSize, router, slug])

  const downloadImage = (src) => {
    if (!src) return
    const link = document.createElement("a")
    link.href = src
    link.download = `${event?.title || "event"}_photo.jpg`
    link.rel = "noopener"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleImageClick = (src, image) => {
    const imageSrc = image?.fullSrc || src
    const isMobile = typeof window !== "undefined"
      && window.matchMedia("(max-width: 1023px)").matches

    if (isMobile) {
      downloadImage(imageSrc)
      return
    }

    setSelectedImage({ src: imageSrc })
  }

  if (!event) {
    return (
      <div style={{ minHeight: "100svh", background: "#080808", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>Event not found.</p>
      </div>
    )
  }
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

          <div style={{ padding: "0 clamp(24px,4vw,56px) 80px" }}>
            <MasonryGallery
              images={images}
              eagerCount={4}
              onEagerLoaded={prefetchNextPage}
              onImageClick={handleImageClick}
            />
          </div>

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
