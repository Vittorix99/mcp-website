"use client"

import { usePathname } from "next/navigation"
import { Navigation } from "@/components/Navigation"

export const TopBar = () => {
  const pathname = usePathname()
  if (
    pathname?.startsWith("/admin") ||
    pathname?.startsWith("/login") ||
    pathname?.startsWith("/dashboard") ||
    pathname?.endsWith("/guide")
  ) return null
  return <Navigation />
}

export default TopBar
