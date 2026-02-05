"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { login, getIdTokenResult } from "@/config/firebase"
import { routes } from "@/config/routes"
import { useUser } from "@/contexts/userContext"
import { Loader2, LogIn } from "lucide-react"

export default function LoginModal({ open, onOpenChange, hideTrigger = false }) {
  const [internalOpen, setInternalOpen] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { setUser, setIsAdmin } = useUser()

  const handleEmailLogin = async (e) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      const result = await login(email, password)
      if (result?.error) {
        setError(result.error)
        return
      }
      const user = result?.user
      const token = await getIdTokenResult()

      setUser(user)
      handleOpenChange(false)

      if (!!token.claims.admin) {
        setIsAdmin(token.claims.admin)
        router.push(routes.admin.dashboard)
      } else {
        router.push(routes.home)
      }
    } catch (error) {
      setError("Si è verificato un errore durante il login")
      console.error("Login error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fadeIn = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 },
  }

  const isControlled = typeof open === "boolean"
  const currentOpen = isControlled ? open : internalOpen

  const handleOpenChange = (nextOpen) => {
    if (!isControlled) {
      setInternalOpen(nextOpen)
    }
    if (onOpenChange) {
      onOpenChange(nextOpen)
    }
  }

  return (
    <Dialog open={currentOpen} onOpenChange={handleOpenChange}>
      {!hideTrigger && (
        <DialogTrigger asChild>
          <Button variant="ghost" className="text-white hover:text-mcp-orange transition-colors">
            LOGIN
          </Button>
        </DialogTrigger>
      )}
      <DialogContent className="sm:max-w-[430px] bg-black/90 border-white/10 login-modal">
        <DialogHeader>
          <DialogTitle className="font-helvetica text-3xl md:text-4xl font-bold tracking-atlantico-wider login-modal__title">
            Login to MCP
          </DialogTitle>
        </DialogHeader>
        <motion.form
          onSubmit={handleEmailLogin}
          className="space-y-6 py-4"
          initial="initial"
          animate="animate"
          exit="exit"
          variants={fadeIn}
        >
          <div className="space-y-2">
            <Label htmlFor="email" className="text-gray-300">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-black/40 border-white/15 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300 login-modal__input"
              placeholder="Enter your email"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password" className="text-gray-300">
              Password
            </Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-black/40 border-white/15 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300 login-modal__input"
              placeholder="Enter your password"
              required
            />
          </div>
          <AnimatePresence>
            {error && (
              <motion.p
                className="text-red-500 text-sm"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>
          <Button
            type="submit"
            className="w-full login-modal__cta py-2 rounded-full transition-all duration-300 transform hover:scale-[1.02] flex items-center justify-center"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Logging in...
              </>
            ) : (
              <>
                <LogIn className="mr-2 h-4 w-4" />
                Login
              </>
            )}
          </Button>
        </motion.form>
      </DialogContent>
    </Dialog>
  )
}
