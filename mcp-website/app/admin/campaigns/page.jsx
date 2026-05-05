"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { routes } from "@/config/routes"
import { AdminLoading } from "@/components/admin/AdminPageChrome"

export default function CampaignsRedirect() {
  const router = useRouter()
  useEffect(() => {
    router.replace(routes.admin.sender.campaigns)
  }, [router])
  return <AdminLoading label="Reindirizzamento..." />
}
