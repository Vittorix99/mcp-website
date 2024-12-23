'use client'

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Image from "next/image";
import Link from "next/link";
import { getNextEvent } from '@/services/events';
import { getImageUrl } from '@/firebase'; // Importa la funzione getImageUrl

export function NextEventSection() {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [imageError, setImageError] = useState(false); // Nuovo stato per gestire l'errore dell'immagine

  useEffect(() => {
    async function fetchNextEvent() {
      try {
        const response = await getNextEvent();
        if (response.success) {
          setEvent(response.event);
          const url = await getImageUrl('events', `${response.event.image}.jpg`);
          setImageUrl(url);
        } else {
          setError(response.error || 'Unable to fetch the next event.');
        }
      } catch (err) {
        setError('Unexpected error occurred while fetching the next event.');
      } finally {
        setLoading(false);
      }
    }
    fetchNextEvent();
  }, []);

  if (loading) {
    return (
      <section className="py-24 bg-black/50 backdrop-blur-md">
        <div className="container mx-auto px-4">
          <h2 className="text-5xl font-extrabold mb-12 text-center text-orange-500 uppercase">
            Next Event
          </h2>
          <div className="text-center text-orange-200">Loading...</div>
        </div>
      </section>
    );
  }



  if (!event) {
    return (
      <section className="py-24 bg-black/50 backdrop-blur-md">
        <div className="container mx-auto px-4">
          <h2 className="text-5xl font-extrabold mb-12 text-center text-orange-500 uppercase">
            Next Event
          </h2>
          <div className="text-center text-orange-200">No upcoming events scheduled</div>
        </div>
      </section>
    );
  }

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

  const filteredLineup = event.lineup.filter((artist) => artist.trim() !== '');

  return (
    <section className="py-24 bg-black/50 backdrop-blur-md">
      <div className="container mx-auto px-4">
        <h2 className="text-5xl font-extrabold mb-12 text-center text-orange-500 uppercase">
          Next Event
        </h2>
        <Card className="max-w-4xl mx-auto bg-black/50 border border-orange-500">
          <CardContent className="p-8">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className="text-3xl font-bold mb-4 text-orange-500">{event.title}</h3>
                <p className="text-lg mb-4 text-orange-200">
                  {formattedDate} | {event.startTime} - {event.endTime}
                </p>
                <div className="space-y-2 mb-6">
                  <p className="text-orange-200">Featuring:</p>
                  {filteredLineup.length > 0 ? (
                    <ul className="list-disc list-inside text-orange-300">
                      {filteredLineup.map((artist, index) => (
                        <li key={index}>{artist}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-orange-200 italic">No lineup available</p>
                  )}
                  {event.location && (
                    <p className="mt-4 text-orange-200">
                      Location: <span className="font-bold">{event.location}</span>
                    </p>
                  )}
           
                </div>
                {event.active ? (
              <Link href={`/events/${event.id}`}>
                <Button className="bg-orange-500 hover:bg-orange-600 text-black font-bold">
                  Tickets & Info
                </Button>
              </Link>
            ) : (
              <Button 
                className="bg-gray-500 cursor-not-allowed text-black font-bold" 
                disabled
              >
                Coming Soon
              </Button>
            )}
              </div>
              <div className="aspect-square relative">
                {imageUrl && !imageError ? (
                  <Image
                    src={imageUrl}
                    alt={event.title}
                    fill
                    className="object-cover rounded-lg"
                    onError={() => setImageError(true)} // Imposta l'errore se il caricamento fallisce
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-800 rounded-lg">
                    <p className="text-orange-200 text-sm italic">Image not available</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}