'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Image from 'next/image'
import { MapPin, Calendar, Clock, Users, Info, Timer } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { getEventById, getAllEvents } from '@/services/events'
import { getImageUrl } from '@/firebase'
import { PayPalSection } from '@/components/pages/PayPalSection'
import React from 'react'



export default function EventPage({id}) {
  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)

  const splitBrText = (text) => {
    // Converte i caratteri \n letterali in veri caratteri di nuova riga
    const processedText = text.replace(/\\n/g, '\n');
    // Divide il testo su ogni nuova riga
    return processedText.split('\n');
  };
  
  

  useEffect(() => {
    async function fetchEvent() {
      try {
        const response = await getEventById(id)
        if (response?.success && response?.event) {
          setEvent(response.event)
          if (response.event) {
            const url = await getImageUrl('events', `${response.event.image}.jpg`)
            setImageUrl(url)
          }
        } else {
          setError(response?.error || 'Impossibile recuperare i dettagli dell\'evento.')
        }
      } catch (err) {
        setError('Evento non disponibile al momento')
      } finally {
        setLoading(false)
      }
    }
    fetchEvent()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4">
          <div className="text-center text-orange-500">Caricamento...</div>
        </div>
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4">
          <Alert className="bg-orange-500/10 border-orange-500/20">
            <AlertDescription className="text-orange-200 text-center text-lg">
              {error || 'Evento non disponibile al momento'}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  // Safely format date with fallback
  let formattedDate = '';
  try {
    const [day, month, year] = event.date?.split('-').map(Number);
  
    // Rebuild the date string manually
    formattedDate = `${day.toString().padStart(2, '0')}-${month
      .toString()
      .padStart(2, '0')}-${year}`;
  } catch (e) {
    formattedDate = event.date || 'Data da definire';
  }
  return (
    <div className="min-h-screen  py-24 relative">
      <div className="container mx-auto px-4">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold text-orange-500 mb-6">
            {event.title || 'Evento'}
          </h2>
          <div className="flex flex-wrap justify-center gap-6 text-orange-200">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              <span>{formattedDate}</span>
            </div>
            {event.startTime && event.endTime && (
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                <span>{event.startTime} - {event.endTime}</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              {event.location === "Private" ? (
                <span className="italic">Location comunicata privatamente</span>
              ) : (
                <span>{event.location || 'Location da definire'}</span>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <Card className="max-w-6xl mx-auto bg-black/50 border border-orange-500 mb-8">
          <CardContent className="p-8">
            {/* Image Section */}
            <div className="max-w-2xl mx-auto mb-12">
              {imageUrl ? (
                <div className="relative w-full" style={{ paddingTop: '56.25%' }}> {/* 16:9 Aspect Ratio */}
                  <Image
                    src={imageUrl}
                    alt={event.title || 'Event image'}
                    fill
                    className="object-contain rounded-lg"
                    priority
                  />
                </div>
              ) : (
                <div className="w-full bg-gray-800 rounded-lg" style={{ paddingTop: '56.25%' }}>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <p className="text-orange-200 text-sm italic">Immagine non disponibile</p>
                  </div>
                </div>
              )}
            </div>

            {/* Event Details Grid */}
            <div className="grid lg:grid-cols-2 gap-8 mb-8">
              {/* Left Column - Event Info */}
              <div className="space-y-6">
                <div className="space-y-4">
                  {event.lineup && event.lineup.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-orange-200">
                        <Users className="w-5 h-5" />
                        <span className="text-lg font-semibold">Lineup:</span>
                      </div>
                      <ul className="list-disc list-inside text-orange-300 ml-7">
                        {event.lineup.map((artist, index) => (
                          <li key={index} className="text-lg">{artist}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {event.minimumAge && (
                    <div className="flex items-center gap-2 text-orange-200">
                      <Info className="w-5 h-5" />
                      <span className="text-lg">Età minima: {event.minimumAge}+</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column - Additional Info */}
              <div className="space-y-6">
                {event.dresscode && (
                  <div className="flex items-center gap-2 text-orange-200">
                    <Info className="w-5 h-5" />
                    <span className="text-lg">Dress code: {event.dresscode}</span>
                  </div>
                )}

                {event.price && (
                  <div className="flex items-center gap-2 text-orange-200">
                    <Timer className="w-5 h-5" />
                    <span className="text-lg">Prezzo: {event.price}€</span>
                  </div>
                )}
              </div>
            </div>

            {/* Notes Section - Full Width */}
            {event.note && (
              <div className="mt-8">
              
                
        
        {splitBrText(event.note).map((line, index) => ( 
          <div key={index} className="text-orange-200 text-lg leading-relaxed">
 
                <span
                className="text-orange-200 text-lg leading-relaxed"
                style={{ whiteSpace: 'pre-wrap' }}
                >       
                {line}
                </span>
                <br />
                </div>
                  
                  ))}
            </div>
                
                
                )}

              



     

            {/* Action Button */}
            <div className="mt-8 flex justify-center">
              {event.active ? (
                <PayPalSection/>
          
              ) : (
                <Button 
                  className="bg-gray-500 text-black font-bold text-lg px-8 py-6 cursor-not-allowed opacity-50" 
                  disabled
                >
                  Biglietti non disponibili
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}