"use client"

import { useState } from "react"
import Image from "next/image"
import { Loader2 } from "lucide-react"

export default function EventImage({ imageUrl, title }) {
  const [imgLoading, setImgLoad] = useState(true)

  return (
    <div className="relative rounded-lg overflow-hidden">
      {imgLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
        </div>
      )}
      {imageUrl ? (
        <Image
          src={imageUrl}
          alt={title || "Event image"}
          sizes="(max-width:768px)100vw,33vw"
          width={500}
          height={200}
          style={{ objectFit: "contain" }}
          onLoadingComplete={() => setImgLoad(false)}
          className="mx-auto"
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
          <p className="text-gray-400 text-sm italic">Image not available</p>
        </div>
      )}
    </div>
  )
}