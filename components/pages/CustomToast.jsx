import { motion } from "framer-motion"
import { X, CheckCircle, AlertCircle } from "lucide-react"

export const CustomToast = ({ message, type, onClose }) => {
  const variants = {
    initial: { opacity: 0, y: 50, scale: 0.3 },
    animate: { opacity: 1, y: 0, scale: 1 },
    exit: { opacity: 0, scale: 0.5, transition: { duration: 0.2 } },
  }

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case "error":
        return <AlertCircle className="w-6 h-6 text-red-500" />
      default:
        return <AlertCircle className="w-6 h-6 text-mcp-orange" />
    }
  }

  return (
    <motion.div
      variants={variants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`fixed bottom-4 right-4 max-w-md w-full bg-black border ${
        type === "success" ? "border-green-500" : "border-red-500"
      } rounded-lg shadow-lg overflow-hidden`}
    >
      <div className="flex items-center p-4">
        <span className="mr-3">{getIcon()}</span>
        <p className="flex-1 text-white">{message}</p>
        <button onClick={onClose} className="ml-3 text-gray-400 hover:text-white">
          <X size={18} />
        </button>
      </div>
      <motion.div
        initial={{ width: "100%" }}
        animate={{ width: "0%" }}
        transition={{ duration: 5 }}
        className={`h-1 ${type === "success" ? "bg-green-500" : "bg-red-500"}`}
      />
    </motion.div>
  )
}

