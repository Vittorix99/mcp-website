"use client"

import { motion } from "framer-motion"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function SignupRequestsPage() {
  return (
    <motion.div
      className="max-w-2xl mx-auto mt-10 space-y-6 text-center text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <AdminPageHeader title="Richieste Signup" />
      <p className="text-lg text-gray-400">
        Questa sezione non è ancora disponibile.
      </p>
      <p className="text-md text-gray-500">
        Sarà attivata nella prossima release della piattaforma MCP Admin.
      </p>
    </motion.div>
  )
}
