"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Loader2, Search } from "lucide-react"
import { Suspense } from "react"
import "@/app/style/admin.css"

import { useUser } from "@/contexts/userContext"
import { useIsMobile } from "@/hooks/use-mobile"
import { CustomSidebar } from "@/components/admin/custom-sidebar"
import { CustomToast } from "@/components/CustomToast"
import { ErrorProvider } from "@/contexts/errorContext"

import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import { routes } from "@/config/routes"

export default function AdminLayout({ children }) {
  const { user, isAdmin, loading } = useUser()
  const isMobile = useIsMobile()
  const router = useRouter()
  const [toast, setToast] = useState(null)

  const fadeIn = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 },
  }

  // Redirect se non admin o se non ammesso da mobile
  useEffect(() => {
    const allowMobile = process.env.NEXT_PUBLIC_ADMIN_ON_MOBILE === "true"
     if (!loading && (!user || !isAdmin)) {
      router.push(routes.error.notAdmin)
    }
 
  }, [user, isAdmin, loading, isMobile, router])

  useEffect(() => {
    const handler = e => e.detail && setToast({ message: e.detail, type: "error" })
    window.addEventListener("errorToast", handler)
    return () => window.removeEventListener("errorToast", handler)
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black">
        <motion.div initial="initial" animate="animate" variants={fadeIn} className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-orange-500 mb-4" />
          <p className="text-xl font-semibold text-orange-500">Loading...</p>
        </motion.div>
      </div>
    )
  }

  if (!user || !isAdmin) return null

  return (
    <ErrorProvider>
      <SidebarProvider>
        <Suspense fallback={<div className="p-4 text-white">Loading...</div>}>
          <div className={`flex min-h-screen w-full flex-col bg-black text-white admin-layout ${!isMobile ? "mt-4" : ""}`}>
            <CustomSidebar />
            <SidebarInset className="admin-header">
              <SidebarTrigger className="sm:hidden " />
              <motion.main
                initial="initial"
                animate="animate"
                variants={fadeIn}
                className="flex-1 overflow-y-auto mx-2 p-4 sm:px-6 md:py-0 md:gap-8 admin-content md:mt-12"
              >
                {children}
              </motion.main>
            </SidebarInset>

            <AnimatePresence>
              {toast && (
                <CustomToast
                  message={toast.message}
                  type={toast.type}
                  onClose={() => setToast(null)}
                />
              )}
            </AnimatePresence>
          </div>
        </Suspense>
      </SidebarProvider>
    </ErrorProvider>
  )
}