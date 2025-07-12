"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Users,
  Wallet,
  ShoppingCart,
  DollarSign,
  RefreshCw,
  Loader2,
  ArrowRight,
  CalendarIcon,
  CreditCard,
  MailWarning,
  MessageSquare,
} from "lucide-react"

// Servizi API
import { getAdminStats } from "@/services/admin/stats"
import { getNextEvent } from "@/services/events"

// Funzioni di utilità
const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return "-"
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(amount)
}

const formatDate = (dateString) => {
  if (!dateString) return "-"
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      const parts = dateString.split("-")
      if (parts.length === 3) {
        // Assumendo dd-mm-yyyy
        return new Date(`${parts[2]}-${parts[1]}-${parts[0]}`).toLocaleDateString("it-IT", {
          day: "numeric",
          month: "long",
          year: "numeric",
        })
      }
      return dateString
    }
    return date.toLocaleDateString("it-IT", { day: "numeric", month: "long", year: "numeric" })
  } catch (e) {
    return dateString
  }
}

const getInitials = (name = "", surname = "") => {
  return `${name.charAt(0)}${surname.charAt(0)}`.toUpperCase()
}

const extractEventNameFromUrl = (url) => {
  if (!url) return "Evento sconosciuto"
  try {
    const parts = url.split("/")
    const encodedName = parts[parts.length - 2]
    return decodeURIComponent(encodedName)
  } catch (e) {
    return "Evento sconosciuto"
  }
}

const StatCard = ({ title, value, icon: Icon, description }) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <Icon className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {description && <p className="text-xs text-muted-foreground">{description}</p>}
    </CardContent>
  </Card>
)

const LoadingSkeleton = () => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <div className="h-9 w-64 bg-gray-700 rounded animate-pulse"></div>
        <div className="h-6 w-40 bg-gray-700 rounded mt-2 animate-pulse"></div>
      </div>
      <div className="h-10 w-28 bg-gray-700 rounded animate-pulse"></div>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-28 bg-gray-800 rounded-lg animate-pulse"></div>
      ))}
    </div>
    <div className="grid lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 h-48 bg-gray-800 rounded-lg animate-pulse"></div>
      <div className="h-96 bg-gray-800 rounded-lg animate-pulse"></div>
    </div>
  </div>
)

export default function AdminDashboard() {
  const router = useRouter()
  const { toast } = useToast()
  const [stats, setStats] = useState(null)
  const [nextEvent, setNextEvent] = useState(null)
  const [loading, setLoading] = useState(true)
const loadAll = async () => {

  setLoading(true)
  try {
    const [statsResp, eventResp] = await Promise.all([
      getAdminStats(),
      getNextEvent()
    ])


    const parsedStats = {
      ...statsResp,
      total_purchases: Number(statsResp?.total_purchases || 0),
      total_gross_amount: Number(statsResp?.total_gross_amount || 0),
      total_net_amount: Number(statsResp?.total_net_amount || 0),
      last_24h_unanswered_messages: Number(statsResp?.last_24h_unanswered_messages || 0),
    }

    setStats(parsedStats)

    if (eventResp?.success && eventResp.event) {
      setNextEvent(eventResp.event)
    } else {
      console.warn("[loadAll] Nessun prossimo evento trovato.")
      setNextEvent(null)
    }
  } catch (e) {
    console.error("[loadAll] Errore durante il caricamento:", e)
    toast({
      variant: "destructive",
      title: "Errore",
      description: e.message || "Errore durante il caricamento dei dati.",
    })
  } finally {
    setLoading(false)
  }
}

useEffect(() => {
  loadAll()
}, [])

  useEffect(() => {
    loadAll()
  }, [])

  if (loading && !stats) {
    return (
      <div className="p-8">
        <LoadingSkeleton />
      </div>
    )
  }

  return (
    <motion.div
      className="p-4 sm:p-6 md:p-8 space-y-6 text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl text-center tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground">Statistiche e attività recenti.</p>
        </div>
        <Button onClick={loadAll} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Aggiorna
        </Button>
      </div>

      {/* Griglia Statistiche Principali */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Incasso Lordo"
          value={formatCurrency(stats?.total_gross_amount)}
          icon={DollarSign}
          description="Totale di tutte le transazioni"
        />
        <StatCard
          title="Incasso Netto"
          value={formatCurrency(stats?.total_net_amount)}
          icon={Wallet}
          description="Al netto delle commissioni"
        />
        <StatCard
          title="Membri Attivi"
          value={stats?.total_active_members ?? "-"}
          icon={Users}
          description="Membri con abbonamento valido"
        />
        <StatCard
          title="Acquisti Totali"
          value={stats?.total_purchases ?? "-"}
          icon={ShoppingCart}
          description="Numero totale di acquisti"
        />
        <StatCard
          title="Messaggi non letti (24h)"
          value={stats?.last_24h_unanswered_messages ?? "-"}
          icon={MailWarning}
          description="Dal form di contatto"
        />
      </div>

      {/* Prossimo Evento e Attività Recenti */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {nextEvent ? (
            <Card className="bg-gray-900/50 border-orange-500/30">
              <CardHeader>
                <CardTitle className="text-orange-400">Prossimo Evento</CardTitle>
                <CardDescription>{nextEvent.title}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2 text-lg">
                      <CalendarIcon className="h-5 w-5" />
                      <span>{formatDate(nextEvent.date)}</span>
                    </div>
                    <div className="mt-2 space-y-1">
                      <p>
                        <strong>Partecipanti:</strong> {stats?.upcoming_event_participants ?? "0"}
                      </p>
                      <p>
                        <strong>Incasso evento:</strong> {formatCurrency(stats?.upcoming_event_total_paid)}
                      </p>
                    </div>
                  </div>
                  <Button onClick={() => router.push(`/admin/events/${nextEvent.id}`)}>
                    Gestisci Evento <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <p>Nessun evento imminente in programma.</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Attività Recenti */}
        <div className="lg:row-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Attività Recenti</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {stats?.last_message && (
                <div className="flex items-center gap-4">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback>
                      <MessageSquare />
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid gap-1 overflow-hidden">
                    <p className="text-sm font-medium leading-none">Ultimo Messaggio</p>
                    <p className="text-sm text-muted-foreground truncate">
                      Da: {stats.last_message.name} - "{stats.last_message.message}"
                    </p>
                  </div>
                </div>
              )}
              {stats?.last_purchase && (
                <div className="flex items-center gap-4">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback>
                      <CreditCard />
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid gap-1">
                    <p className="text-sm font-medium leading-none">Ultimo Acquisto</p>
                    <p className="text-sm text-muted-foreground">
                      {stats.last_purchase.payer_name} {stats.last_purchase.payer_surname} -{" "}
                      {formatCurrency(stats.last_purchase.amount_total)}
                    </p>
                  </div>
                </div>
              )}
              {stats?.last_membership && (
                <div className="flex items-center gap-4">
                  <Avatar className="h-9 w-9">
                    <AvatarImage
                      src={`https://api.dicebear.com/7.x/initials/svg?seed=${stats.last_membership.name} ${stats.last_membership.surname}`}
                    />
                    <AvatarFallback>
                      {getInitials(stats.last_membership.name, stats.last_membership.surname)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid gap-1">
                    <p className="text-sm font-medium leading-none">Nuovo Membro</p>
                    <p className="text-sm text-muted-foreground">
                      {stats.last_membership.name} {stats.last_membership.surname}
                    </p>
                  </div>
                </div>
              )}
              {stats?.last_participant && (
                <div className="flex items-center gap-4">
                  <Avatar className="h-9 w-9">
                    <AvatarImage
                      src={`https://api.dicebear.com/7.x/initials/svg?seed=${stats.last_participant.name} ${stats.last_participant.surname}`}
                    />
                    <AvatarFallback>
                      {getInitials(stats.last_participant.name, stats.last_participant.surname)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid gap-1 overflow-hidden">
                    <p className="text-sm font-medium leading-none">Nuovo Partecipante</p>
                    <p className="text-sm text-muted-foreground truncate">
                      {stats.last_participant.name} {stats.last_participant.surname} per{" "}
                      {extractEventNameFromUrl(stats.last_participant.ticket_pdf_url)}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  )
}
