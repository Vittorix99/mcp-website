"use client"

import { useState, useEffect, Suspense } from "react"
import { AnimatePresence } from "framer-motion"
import { getEventById } from "@/services/events"
import { getImageUrls } from "@/config/firebase"
import { Loader2 } from "lucide-react"
import ImageModal from "@/components/pages/modals/ImageModal"
import { MasonryGallery } from "@/components/pages/pictures/MasonGallery"
import { SectionTitle } from "@/components/ui/section-title"

export function EventContent({id}) {

  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imageUrls, setImageUrls] = useState([])

  useEffect(() => {
    async function fetchEventAndPhotos() {
      try {
        const eventResponse = await getEventById(id)
        if (eventResponse?.success && eventResponse?.event) {
          setEvent(eventResponse.event)
          const photoUrls = await getImageUrls(`foto/${eventResponse.event.title}`)
          const formattedImageUrls = photoUrls.map((url, index) => ({
            src: url,
            alt: `${eventResponse.event.title} - Photo ${index + 1}`,
          }))
          setImageUrls(formattedImageUrls)
        } else {
          setError("Unable to retrieve event details.")
        }
      } catch (err) {
        setError("An error occurred while fetching event data.")
      } finally {
        setLoading(false)
      }
    }
    fetchEventAndPhotos()
  }, [id])

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
      <div className="container mx-auto px-4">

     
        <SectionTitle as="h1" className="mt-8">
          Event Photos
        </SectionTitle>
        <MasonryGallery images={imageUrls} />
      </div>

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
