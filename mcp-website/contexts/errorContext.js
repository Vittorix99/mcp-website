"use client"

import { createContext, useContext, useCallback } from "react"

const ErrorContext = createContext({
  setError: (msg) => {},
})

export function ErrorProvider({ children }) {
  const setError = useCallback((message) => {
    if (!message) return
    window.dispatchEvent(new CustomEvent("errorToast", {
      detail: message
    }))
  }, [])

  return (
    <ErrorContext.Provider value={{ setError }}>
      {children}
    </ErrorContext.Provider>
  )
}

export const useError = () => useContext(ErrorContext)