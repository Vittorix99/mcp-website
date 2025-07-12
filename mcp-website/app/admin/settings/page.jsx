"use client"

import { useEffect, useState } from "react"
import { ArrowLeft, Save, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { getAllSettings, setSetting } from "@/services/admin/settings"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { toast } from "sonner"
import { motion } from "framer-motion"

export default function SettingsPage() {
  const router = useRouter()
  const [settings, setSettings] = useState(null)
  const [loadingKey, setLoadingKey] = useState(null)

  useEffect(() => {
    getAllSettings()
      .then((res) => {
        if (res.error) {
          toast.error(`Errore: ${res.error}`)
        } else if (res.settings && typeof res.settings === "object") {
          setSettings(res.settings)
        } else {
          toast.error("Formato risposta non valido")
        }
      })
      .catch(() => toast.error("Errore di rete"))
  }, [])

  const handleValueChange = (key, newValue) => {
    setSettings(prev => ({ ...prev, [key]: newValue }))
  }

  const handleSave = async (key) => {
    setLoadingKey(key)
    const result = await setSetting(key, settings[key])
    if (result.error) {
      toast.error(`Errore salvataggio "${key}": ${result.error}`)
    } else {
      toast.success(`"${key}" salvata con successo ✅`)
    }
    setLoadingKey(null)
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-screen text-white">
        <Loader2 className="animate-spin h-8 w-8" />
      </div>
    )
  }

  return (
    <motion.div
      className="max-w-3xl mx-auto mt-10 space-y-6 text-white px-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Torna indietro
      </Button>

      <h1 className="text-3xl font-bold">⚙️ Impostazioni</h1>

      <div className="space-y-4">
        {Object.entries(settings).map(([key, value]) => (
          <div
            key={key}
            className="flex flex-col sm:flex-row items-center gap-4 p-4 bg-zinc-900 border border-zinc-700 rounded-lg"
          >
            <div className="font-mono text-sm w-full sm:w-1/3">{key}</div>

            {typeof value === "boolean" ? (
              <Switch
                checked={value}
                onCheckedChange={(v) => handleValueChange(key, v)}
              />
            ) : (
              <Input
                className="flex-1"
                value={String(value)}
                onChange={(e) => handleValueChange(key, e.target.value)}
              />
            )}

            <Button
              size="sm"
              onClick={() => handleSave(key)}
              disabled={loadingKey === key}
            >
              {loadingKey === key ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" /> Salva
                </>
              )}
            </Button>
          </div>
        ))}
      </div>
    </motion.div>
  )
}