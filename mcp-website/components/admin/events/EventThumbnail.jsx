import { getImageUrl } from "@/config/firebaseStorage"
import { useState, useEffect } from "react"

export function EventThumbnail({ imageName, alt }) {
  const [url, setUrl] = useState(null)

  useEffect(() => {
    let mounted = true
    getImageUrl("events", `${imageName}.jpg`)
      .then(u => { if (mounted) setUrl(u) })
      .catch(err => console.error("Fetch img failed:", err))
    return () => { mounted = false }
  }, [imageName])

  if (!url) return <div className="w-16 h-16 bg-gray-800 rounded animate-pulse" />
  return <img src={url} alt={alt} className="w-16 h-16 object-cover rounded" />
}