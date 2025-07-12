"use client"

import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const MAX_TICKETS = parseInt(process.env.NEXT_PUBLIC_MAX_TICKETS || "5")

export default function QuantitySelector({ quantity, setQuantity, disabled = false }) {
  const handleQuantityChange = (e) => {
    const value = Number.parseInt(e.target.value)
    if (!isNaN(value) && value >= 1 && value <= MAX_TICKETS) {
      setQuantity(value)
    }
  }

  return (
    <div className="space-y-2 mt-6">
      <Label htmlFor="quantity" className="text-white text-sm">
        Quantità
      </Label>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="h-8 w-8 border border-gray-700 text-white flex items-center justify-center rounded-md"
          onClick={() => quantity > 1 && setQuantity(quantity - 1)}
          disabled={quantity <= 1 || disabled}
        >
          -
        </button>
        <Input
          id="quantity"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          min="1"
          max={MAX_TICKETS}
          value={quantity}
          disabled={disabled}
          onChange={handleQuantityChange}
          className="bg-black/50 border-gray-700 text-white text-center"
        />
        <button
          type="button"
          className="h-8 w-8 border border-gray-700 text-white flex items-center justify-center rounded-md"
          onClick={() => quantity < MAX_TICKETS && setQuantity(quantity + 1)}
          disabled={quantity >= MAX_TICKETS || disabled}
        >
          +
        </button>
      </div>
      <p className="text-xs text-gray-400">Massimo {MAX_TICKETS} biglietti per acquisto</p>
    </div>
  )
}