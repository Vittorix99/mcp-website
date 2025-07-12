import { useEffect, useState, useCallback, useMemo } from "react"
import { useError } from "@/contexts/errorContext"
import {
  getAllMessages,
  getMessageById,
  deleteMessage,
  replyToMessage,
} from "@/services/admin/messages"

export function useAdminMessages() {
  const { setError } = useError()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const loadMessages = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getAllMessages()
      if (data?.error) {
        setError(data.error)
      } else {
        setMessages(data || [])
      }
    } catch (err) {
      console.error("Errore caricamento messaggi:", err)
      setError("Impossibile caricare i messaggi.")
    } finally {
      setLoading(false)
    }
  }, [setError])

  useEffect(() => {
    loadMessages()
  }, [loadMessages])

  const reload = () => loadMessages()

  const handleDelete = async (messageId) => {
    const res = await deleteMessage(messageId)
    if (res?.error) {
      setError(res.error)
    } else {
      loadMessages()
    }
  }

  const handleReply = async ({ email, body, subject = "Risposta al tuo messaggio", message_id }) => {
    const res = await replyToMessage({ email, body, subject, message_id })
    if (res?.error) {
      setError(res.error)
    }
    return res
  }

  // 📊 Statistiche derivate dai messaggi
  const total = messages.length
  const last24h = useMemo(() => {
    const now = Date.now()
    const oneDay = 24 * 60 * 60 * 1000
    return messages.filter(m => {
      const ts = m.timestamp?.seconds ? m.timestamp.seconds * 1000 : new Date(m.timestamp).getTime()
      return now - ts < oneDay
    }).length
  }, [messages])

  const answeredCount = useMemo(() => messages.filter(m => m.answered).length, [messages])

  return {
    messages,
    loading,
    reload,
    deleteMessage: handleDelete,
    replyToMessage: handleReply,
    getMessageById,
    total,
    last24h,
    answeredCount,
  }
}