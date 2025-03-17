"use client"

import { useEffect, useState } from "react"

export function PolicyLinks() {
  const [iubendaLoaded, setIubendaLoaded] = useState(false)

  useEffect(() => {
    // Verifica se iubenda è stato caricato
    const checkIubenda = () => {
      if (window._iub) {
        setIubendaLoaded(true)
        return true
      }
      return false
    }

    // Se iubenda non è ancora caricato, controlla ogni 500ms
    if (!checkIubenda()) {
      const interval = setInterval(() => {
        if (checkIubenda()) {
          clearInterval(interval)
        }
      }, 500)

      return () => clearInterval(interval)
    }
  }, [])

  const openPreferences = () => {
    if (window._iub && window._iub.cs) {
      window._iub.cs.api.openPreferences()
    }
  }

  return (
    <button
      onClick={openPreferences}
      className="font-helvetica text-xm bg-transparent border-none cursor-pointer text-black hover:text-white transition-colors"
      disabled={!iubendaLoaded}
    >
      Privacy & Cookie Policy
    </button>
  )
}

