"use client"

import { usePathname } from "next/navigation"
import { Navigation } from "@/components/Navigation"

export const TopBar = () => {
  const pathname = usePathname()
  if (pathname === "/") {
    return <Navigation />
  }

  return null
}

export default TopBar
