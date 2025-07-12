"use client"

import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Eye, Send, Loader2 } from "lucide-react" // FIX: Importato Loader2
import { formatFirestoreTimestamp } from "@/lib/utils"

export function MessagesMobileView({ messages, loading, onPreview, onReply }) {
  // FIX: Usato Loader2 per coerenza con la versione desktop
  if (loading)
    return (
      <div className="text-center py-6 flex flex-col items-center gap-2">
        <Loader2 className="animate-spin h-6 w-6" />
        <span>Caricamento...</span>
      </div>
    )

  if (!messages || messages.length === 0)
    return <p className="text-center py-6 text-gray-500">Nessun messaggio trovato.</p>

  return (
    <div className="space-y-4">
      {messages.map(
        (m) =>
          m && ( // Aggiunto controllo per robustezza
            <Card key={m.id} className="bg-zinc-900 border border-zinc-700">
              <CardHeader className="flex flex-row justify-between items-start p-4">
                <div className="overflow-hidden">
                  <h3 className="font-bold truncate">{m.name || "N/D"}</h3>
                  <p className="text-sm text-gray-400 truncate">{m.email || "N/D"}</p>
                </div>
                <div className="flex space-x-1 flex-shrink-0">
                  <Button size="icon" variant="ghost" onClick={() => onPreview(m)}>
                    <Eye className="h-5 w-5" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => onReply(m)}>
                    <Send className="h-5 w-5" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <p className="text-sm truncate" title={m.message}>
                  {m.message || "N/D"}
                </p>
              </CardContent>
              <CardFooter className="p-4 pt-0">
                <p className="text-xs text-gray-500 w-full text-right">
                  {m.timestamp ? formatFirestoreTimestamp(m.timestamp) : "N/D"}
                </p>
              </CardFooter>
            </Card>
          ),
      )}
    </div>
  )
}
