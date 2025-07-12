"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { routes } from "@/config/routes"
import { AlertTriangle, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function NotAdminErrorPage() {
  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  const iconAnimation = {
    initial: { scale: 0 },
    animate: { scale: 1 },
    transition: { type: "spring", stiffness: 260, damping: 20 },
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <section className="relative w-full max-w-md px-4 py-8 flex flex-col items-center justify-center">
        <motion.div className="text-center" initial="initial" animate="animate" variants={fadeInUp}>
          <motion.div initial="initial" animate="animate" variants={iconAnimation} className="mb-6">
            <AlertTriangle className="h-24 w-24 text-mcp-orange mx-auto" />
          </motion.div>
          <h1 className="text-5xl font-bold gradient-text mb-6">Access Denied</h1>
          <p className="text-gray-300 text-xl mb-10">Sorry, you don't have permission to access the admin area.</p>
          <div className="flex justify-center">
            <Link href={routes.home} passHref>
              <Button className="bg-mcp-gradient hover:opacity-90 text-white font-bold py-3 px-6 rounded-md transition-all duration-300 transform hover:scale-105 flex items-center">
                <ArrowLeft className="mr-2 h-5 w-5" />
                Return to Home
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>
    </div>
  )
}

