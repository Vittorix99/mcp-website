"use client"

import { motion } from "framer-motion"
import { X } from "lucide-react"

export function CustomToast({ message, type, onClose }) {
  return (
    <motion.div
      className={`fixed bottom-4 right-4 z-50 p-3 md:p-4 rounded-md shadow-lg max-w-[90vw] md:max-w-sm flex items-center justify-between ${
        type === "success" ? "bg-green-500" : "bg-red-500"
      }`}
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      transition={{ duration: 0.3 }}
    >
      <p className="text-white text-xs md:text-sm font-medium mr-2">{message}</p>
      <button
        onClick={onClose}
        className="text-white hover:text-gray-200 transition-colors"
        aria-label="Close notification"
      >
        <X className="h-4 w-4 md:h-5 md:w-5" />
      </button>
    </motion.div>
  )
}

