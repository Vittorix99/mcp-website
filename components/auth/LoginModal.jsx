'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { auth, googleProvider } from '@/firebase'
import { signInWithEmailAndPassword, signInWithPopup } from 'firebase/auth'

export default function LoginModal() {
  const [isOpen, setIsOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleEmailLogin = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await signInWithEmailAndPassword(auth, email, password)
      setIsOpen(false)
    } catch (error) {
      setError('Invalid email or password')
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setError('')
    setIsLoading(true)

    try {
      await signInWithPopup(auth, googleProvider)
      setIsOpen(false)
    } catch (error) {
      setError('Failed to sign in with Google')
      console.error('Google login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="link" className="text-orange-200 hover:text-orange-500">
          LOGIN
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] bg-black border-orange-500">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-orange-500">Login to MCP</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleEmailLogin} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-orange-200">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50"
              placeholder="Enter your email"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password" className="text-orange-200">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50"
              placeholder="Enter your password"
              required
            />
          </div>
          {error && (
            <p className="text-red-500 text-sm">{error}</p>
          )}
          <Button 
            type="submit" 
            className="w-full bg-orange-500 hover:bg-orange-600 text-black"
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Login with Email'}
          </Button>
        </form>
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <Separator className="w-full border-orange-500/20" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-black px-2 text-orange-200">Or continue with</span>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          className="w-full border-orange-500 text-orange-200 hover:bg-orange-500/10"
          onClick={handleGoogleLogin}
          disabled={isLoading}
        >
          Login with Google
        </Button>
      </DialogContent>
    </Dialog>
  )
}