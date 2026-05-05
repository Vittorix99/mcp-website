"use client"

import { useRouter } from "next/navigation"
import { ArrowLeft, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

const TITLE_CLASS = "text-3xl md:text-4xl font-bold gradient-text tracking-tight"
const SUBTITLE_CLASS = "text-sm text-muted-foreground mt-2"

export function AdminLoading({ label = "Caricamento..." }) {
  return (
    <div className="flex min-h-[320px] items-center justify-center text-white">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-mcp-orange" />
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  )
}

export function AdminInlineLoading({ label = "Caricamento..." }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
      <Loader2 className="h-5 w-5 animate-spin text-mcp-orange" />
      <span>{label}</span>
    </div>
  )
}

export function AdminBackButton({ href, label = "Torna indietro", className = "" }) {
  const router = useRouter()

  const handleClick = () => {
    if (href) {
      router.push(href)
      return
    }
    router.back()
  }

  return (
    <Button variant="ghost" onClick={handleClick} className={`px-0 text-muted-foreground hover:text-white ${className}`}>
      <ArrowLeft className="mr-2 h-4 w-4" />
      {label}
    </Button>
  )
}

export function AdminPageHeader({
  title,
  description,
  backHref,
  backLabel,
  actions,
  showBack = true,
  className = "",
}) {
  return (
    <header className={`mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between ${className}`}>
      <div>
        {showBack && <AdminBackButton href={backHref} label={backLabel} className="mb-2" />}
        <h1 className={TITLE_CLASS}>{title}</h1>
        {description && <p className={SUBTITLE_CLASS}>{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2 sm:justify-end">{actions}</div>}
    </header>
  )
}
