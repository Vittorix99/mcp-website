"use client"

import { useState, useEffect, useMemo } from "react"
import Image from "next/image"
import { motion } from "framer-motion"
import { MapPin, Calendar, Clock, Circle, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { getEventById } from "@/services/events"
import { getImageUrl } from "@/config/firebaseStorage"
import { PayPalSection } from "@/components/pages/events/PayPalSection"

/* -------------------------------------------------------------------------- */
/* helpers                                                                    */
/* -------------------------------------------------------------------------- */

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 },
}

const splitLines = (txt = "") =>
  txt
    .replace(/\\n/g, "\n")
    .split("\n")
    .filter((l) => l.trim() !== "")

const formatDate = (d) => {
  try {
    const [day, month, year] = d.split("-").map(Number)
    return `${String(day).padStart(2, "0")}-${String(month).padStart(2, "0")}-${year}`
  } catch {
    return d || "Date to be announced"
  }
}

/* -------------------------------------------------------------------------- */
/* main component                                                             */
/* -------------------------------------------------------------------------- */

export default function StandardContent({ id }) {
  const [event, setEvent] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [imageUrl, setImage] = useState(null)
  const [imgLoading, setImgLoad] = useState(true)

  useEffect(() => {
    if (!id) {
      setError("No event ID provided")
      setLoading(false)
      return
    }

    ;(async () => {
      try {
        const res = await getEventById(id)
        if (!res?.success || !res.event) throw new Error("not-found")
        setEvent(res.event)

        if (res.event.image) {
          const url = await getImageUrl("events", `${res.event.image}.jpg`)
          setImage(url)
        }
      } catch {
        setError("Event currently unavailable")
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  // ───────────────────────── HOOKS INVARIABILI ─────────────────────────
  const noteLines = useMemo(() => splitLines(event?.note), [event?.note])
  const detailLines = useMemo(() => splitLines(event?.details), [event?.details])
  const lineup      = event?.lineup || []; // array di partecipanti

  // ──────────────────────── RENDER STATE: LOADING ────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="h-24" />
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  // ──────────────────────── RENDER STATE: ERRORE ────────────────────────
  if (error || !event) {
    return (
      <div className="min-h-screen bg-black">
        <div className="h-24" />
        <div className="container mx-auto px-4 pt-16">
          <Alert className="bg-mcp-orange/10 border-mcp-orange/20">
            <AlertDescription className="text-white text-center text-lg font-helvetica">
              {error || "Event currently unavailable"}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  // ─────────────────────────── RENDER COMPLETO ───────────────────────────
  return (
    <div className="min-h-screen bg-black mb-10">

      <div className="container mx-auto px-4 pt-12">



        {/* body */}
        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* image */}
          <div className="relative rounded-lg overflow-hidden">
            {imgLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
              </div>
            )}
            {imageUrl ? (
              <Image
                src={imageUrl}
                alt={event.title || "Event image"}
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

          {/* content */}
          <motion.div
            initial="initial" animate="animate" variants={fadeInUp}
            className="bg-black/30 backdrop-blur-sm rounded-lg border border-mcp-orange/20 p-6"
          >
            {/* price */}
                {event.active ? (
                  <div className="text-center mb-8">
                    <div className="font-atlantico tracking-atlantico-wide text-4xl text-mcp-orange">
                      {event.price ?? "-"}€
                    </div>
                    <div className="font-helvetica text-sm text-gray-400">Prezzo attivo</div>
                  </div>
                ) : (
                  <div className="text-center mb-8">
                    <div className="text-gray-400 text-sm font-helvetica italic">Prezzo non disponibile</div>
                  </div>
                )}

            {/* notes / description / details */}
            <div className="space-y-4">
              {noteLines.map((l, i) => (<Line key={`n${i}`} text={l} />))}

              {event.description && (
                <>
                  {!!noteLines.length && <Spacer />}
                  <Line text={event.description} />
                </>
              )}

              {detailLines.length > 0 && (
                <>
                  <Spacer />
                  {detailLines.map((l, i) => (<Line key={`d${i}`} text={l} />))}
                </>
              )}
            </div>
                {/* LINEUP */}
            {lineup.length > 0 && (
              <div className="mt-8 text-center">
                <h3 className="text-mcp-orange font-bold mb-2">Lineup</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-300">
                  {lineup.map((member, i) => (
                    <li key={i}>{member}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* PayPal */}
            <div className="mt-8">
              {event.active ? (
               <PayPalSection
                  event={event}
                  cart={{ total: parseFloat(event.price) || 0 }}
                />
              ) : (
                <p className="text-center font-helvetica text-gray-300 text-sm py-4">
                  Tickets not available
                </p>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* sub components                                                             */
/* -------------------------------------------------------------------------- */

const Meta = ({ icon: Icon, children }) => (
  <div className="flex items-center text-mcp-orange">
    <Icon className="w-5 h-5 mr-2" />
    <span className="font-helvetica">{children}</span>
  </div>
)

const Line = ({ text }) => (
  <div className="flex">
    <Circle className="w-3 h-3 text-mcp-orange mt-1 mr-3 flex-shrink-0" fill="#FF6B00" />
    <span className="font-helvetica text-gray-300 text-sm">{text}</span>
  </div>
)

const Spacer = () => (
  <div className="flex">
    <Circle className="w-3 h-3 text-transparent mt-1 mr-3 flex-shrink-0" />
    <span className="font-helvetica text-transparent text-sm">&nbsp;</span>
  </div>
)