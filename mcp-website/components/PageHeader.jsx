"use client"

import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { SectionTitle } from "@/components/ui/section-title"

export const PageHeader = ({ title }) => {
  const router = useRouter()

  const handleBack = () => {
    if (window.history.length > 1) {
      router.back()
      return
    }
    router.push("/")
  }

  return (
    <div className="page-header mt-4 mb-8 flex items-center gap-4">
      <Button variant="ghost" className="back-pill" onClick={handleBack} aria-label="Back">
        <ArrowLeft className="h-4 w-4" />
      </Button>
      <SectionTitle as="h1" className="page-header__title">
        {title}
      </SectionTitle>
    </div>
  )
}

export default PageHeader
