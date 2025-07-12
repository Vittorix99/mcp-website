'use client'

import { useEffect } from 'react'

export const ConsoleErrorSilencer = () => {
  useEffect(() => {
    const originalConsoleError = console.error

    console.error = (...args) => {
      const message = args[0]?.toString?.() || ''

      const isGtagNoise =
        message.includes('Actual:   ["set", "ads_data_redaction"]')

        message.includes('Ignored "set" command') ||
        message.includes('Expected: "[set, Object] or [set, string, string]"') ||
        message.includes('Actual:   ["set", "developer_id.dZTJkMz"]') ||
        message.includes('Actual:   ["set", "url_passthrough"]')
        message.includes('Actual:   ["set", "ads_data_redaction"]')



      if (isGtagNoise) {
        return
      }

      originalConsoleError(...args)
    }

    return () => {
      console.error = originalConsoleError
    }
  }, [])

  return null
}