"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { routes } from "@/config/routes"

export default function CampaignsRedirect() {
  const router = useRouter()
  useEffect(() => {
    router.replace(routes.admin.sender.campaigns)
  }, [router])
  return null
}
