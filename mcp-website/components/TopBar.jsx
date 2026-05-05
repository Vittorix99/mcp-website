"use client"

import { usePathname } from "next/navigation"
import { Navigation } from "@/components/Navigation"

export const TopBar = () => {
  const pathname = usePathname()
  // Hide navigation inside admin panel
  if (pathname?.startsWith("/admin")) return null
  return <Navigation />
}

export default TopBar
