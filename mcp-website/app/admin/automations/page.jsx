"use client"

import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { routes } from "@/config/routes"

export default function AutomationsPage() {
  const router = useRouter()

  return (
    <motion.div
      className="max-w-2xl mx-auto mt-10 space-y-6 text-center text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Torna admin
      </Button>

      <h1 className="text-3xl font-bold">Automations</h1>
      <p className="text-lg text-gray-400">
        Questa sezione è in sviluppo.
      </p>
    </motion.div>
  )
}
