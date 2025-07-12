"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Loader2 } from "lucide-react"
import { toast } from "@/hooks/use-toast"

export function PrivateAccessModal({ isOpen, onOpenChange, eventId, eventTitle }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: "",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      // Call your API to send access request
      const response = await fetch("/api/events/private-access", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          eventId,
          ...formData,
        }),
      })

      const data = await response.json()

      if (data.success) {
        toast({
          title: "Request Sent!",
          description: "We've received your request. You'll be notified via email if approved.",
          variant: "success",
        })
        onOpenChange(false)
      } else {
        setError(data.message || "Unable to send request. Please try again.")
      }
    } catch (err) {
      setError("An error occurred. Please try again later.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="bg-black border border-mcp-orange/30 text-white sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-mcp-orange text-xl font-atlantico tracking-atlantico-wide">
            Request Access
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            This is a private event. Submit your details to request access.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-white">
              Full Name
            </Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Your name"
              required
              className="bg-black/50 border-gray-700 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-white">
              Email Address
            </Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your@email.com"
              required
              className="bg-black/50 border-gray-700 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="message" className="text-white">
              Message (Optional)
            </Label>
            <Textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              placeholder="Tell us why you'd like to attend this event..."
              className="bg-black/50 border-gray-700 text-white min-h-[80px]"
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-mcp-orange hover:bg-mcp-orange/90 text-black">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              {loading ? "Sending..." : "Submit Request"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
