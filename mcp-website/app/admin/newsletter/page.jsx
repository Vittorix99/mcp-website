"use client"

import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"

export default function NewsletterPage() {
  const router = useRouter()

  return (
    <motion.div
      className="max-w-2xl mx-auto mt-10 space-y-6 text-center text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Torna indietro
      </Button>

      <h1 className="text-3xl font-bold">Newsletter</h1>
      <p className="text-lg text-gray-400">
        Questa sezione non è ancora disponibile.
      </p>
      <p className="text-md text-gray-500">
        Sarà attivata nella prossima release della piattaforma MCP Admin.
      </p>
    </motion.div>
  )
}