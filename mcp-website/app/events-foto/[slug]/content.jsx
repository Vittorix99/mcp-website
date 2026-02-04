"use client"

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import Link from "next/link"
import { Loader2 } from "lucide-react"
import { MasonryGallery } from "@/components/pages/pictures/MasonGallery"
import { SectionTitle } from "@/components/ui/section-title"
import { Button } from "@/components/ui/button"

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
  const [allLoaded, setAllLoaded] = useState(false)
  const [loadProgress, setLoadProgress] = useState(0)
  const loadProgressRef = useRef(0)
  const images = useMemo(() => pageImages || [], [pageImages])
  const prefetchedRef = useRef(new Set())

  useEffect(() => {
    setAllLoaded(false)
    setLoadProgress(0)
  }, [images.length, currentPage])

  useEffect(() => {
    if (!allLoaded) return
    if (!Array.isArray(prefetchUrls) || prefetchUrls.length === 0) return
    prefetchUrls.forEach((url) => {
      if (!url) return
      if (prefetchedRef.current.has(url)) return
      prefetchedRef.current.add(url)
      const img = new Image()
      img.src = url
    })
  }, [allLoaded, prefetchUrls])

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
  const canNext = currentPage < totalPages && allLoaded
  const canLast = currentPage < totalPages && allLoaded
  const basePath = slug ? `/events-foto/${slug}` : ""
  const pageHref = (page) => (page <= 1 ? basePath : `${basePath}?page=${page}`)
  const hasPhotos = totalLength > 0 || images.length > 0
  const remaining = totalLength
    ? Math.max(0, totalLength - (currentPage - 1) * pageSize)
    : pageSize
  const skeletonCount = Math.max(1, Math.min(pageSize, remaining || pageSize))

  const handleAllLoaded = useCallback(() => {
    setAllLoaded(true)
  }, [])

  const handleProgress = useCallback((ratio) => {
    const next = Math.max(0, Math.min(1, Number.isFinite(ratio) ? ratio : 0))
    const stepped = Math.floor(next * 10) / 10
    if (stepped === loadProgressRef.current) return
    loadProgressRef.current = stepped
    setLoadProgress(stepped)
  }, [])

  return (
    <div className="bg-black py-24">
      <MobileSafe>
        <div className="container mx-auto px-4">
          <SectionTitle as="h1" className="mt-8">
            Event Photos
          </SectionTitle>

          {hasPhotos && !allLoaded && (
            <div className="mt-4 hidden md:flex flex-col items-center justify-center gap-3 text-gray-300">
              <div className="flex items-center gap-2">
                <Loader2 className="w-6 h-6 text-mcp-orange animate-spin" />
                <span className="text-sm md:text-base">Be patient, the images are high quality...</span>
              </div>
              <div className="w-full max-w-md h-2 rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-mcp-orange transition-all duration-300"
                  style={{ width: `${Math.round(loadProgress * 100)}%` }}
                />
              </div>
              <div className="text-xs text-gray-400">{Math.round(loadProgress * 100)}%</div>
            </div>
          )}

          {!hasPhotos ? (
            <div className="mt-6 text-center text-gray-400">No photos available.</div>
          ) : (
            <>
              <div className="flex items-center justify-between mt-4 mb-4">
                <div className="text-sm text-gray-400">
                  Mostrando <span className="text-white">{images.length}</span> su {totalLength}
                </div>
                <div className="flex items-center gap-2">
                  {canPrev ? (
                    <Button variant="outline" size="sm" asChild>
                      <Link href={pageHref(1)} prefetch={false}>
                        « Inizio
                      </Link>
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" disabled>
                      « Inizio
                    </Button>
                  )}
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
                  <span className="text-sm text-gray-300">
                    Pagina <span className="text-white">{currentPage}</span> / {totalPages}
                  </span>
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
                  {canLast ? (
                    <Button variant="outline" size="sm" asChild>
                      <Link href={pageHref(totalPages)} prefetch={false}>
                        Fine »
                      </Link>
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" disabled>
                      Fine »
                    </Button>
                  )}
                </div>
              </div>

              {hasPhotos && !allLoaded && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-1">
                  {Array.from({ length: skeletonCount }).map((_, index) => (
                    <div
                      key={`skeleton-${index}`}
                      className="relative overflow-hidden"
                      style={{ aspectRatio: "1" }}
                    >
                      <div className="absolute inset-0 bg-zinc-900 animate-pulse" />
                    </div>
                  ))}
                </div>
              )}

              <div className={allLoaded ? "opacity-100" : "opacity-0 pointer-events-none"}>
                <MasonryGallery
                  images={images}
                  onAllLoaded={handleAllLoaded}
                  onProgress={handleProgress}
                />
              </div>

              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between">
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
    </div>
  )
}
