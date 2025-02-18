"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@/contexts/userContext"
import { routes } from "@/config/routes"
import { motion } from "framer-motion"
import { Loader2 } from "lucide-react"

export default function AdminLayout({ children }) {
  const { user, isAdmin, loading } = useUser()
  const router = useRouter()

  useEffect(() => {
    if (!loading && (!user || !isAdmin)) {
      router.push(routes.error.notAdmin) // ✅ Now this runs AFTER rendering
    }
  }, [user, isAdmin, loading, router])

  const fadeIn = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 },
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <motion.div initial="initial" animate="animate" variants={fadeIn} className="text-center">
          <Loader2 className="w-12 h-12 text-mcp-orange animate-spin mb-4" />
          <p className="text-mcp-orange text-xl font-semibold">Loading...</p>
        </motion.div>
      </div>
    )
  }

  if (!user || !isAdmin) {
    return null // ❌ Prevent rendering anything before redirection happens
  }

  return (
    <motion.div initial="initial" animate="animate" variants={fadeIn} className="min-h-screen bg-black pt-16">
      <div className="container mx-auto px-4">{children}</div>
    </motion.div>
  )
}