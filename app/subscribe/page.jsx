"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, CheckCircle, XCircle, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { submitSignupRequest } from "@/services/signup"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { SectionTitle } from "@/components/ui/section-title"
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider"

export default function SubscribePage() {
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false)
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()

    const formData = {
      firstName: e.target.firstName.value,
      lastName: e.target.lastName.value,
      email: e.target.email.value,
      instagram: e.target.instagram.value,
    }

    try {
      const result = await submitSignupRequest(formData)
      if (result.success) {
        setIsSubmitted(true)
        setIsSuccessModalOpen(true)
      } else if (result.success === false && result.error) {
        setErrorMessage(result.error)
        setIsErrorModalOpen(true)
      }
    } catch (error) {
      console.error("Signup error:", error)
      setErrorMessage(error.message)
      setIsErrorModalOpen(true)
    }
  }

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Spacer div to push content below navbar */}
      <div className="h-24"></div>

      <div className="container mx-auto px-4 pt-16">
        <SectionTitle as="h1" className="mt-8">
          Join MCP Community
        </SectionTitle>

        <AnimatedSectionDivider color="ORANGE" className="mb-12" />

        <motion.div initial="initial" animate="animate" variants={fadeInUp}>
          <Card className="max-w-2xl mx-auto bg-black/50 backdrop-blur-md border-mcp-orange/50">
            <CardHeader>
              <CardTitle className="text-3xl gradient-text">Become a Member</CardTitle>
              <CardDescription className="text-gray-300">
                Join our community and experience the power of music connection.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="space-y-4">
                <h2 className="text-2xl  gradient-text">Benefits of Joining:</h2>
                <ul className="list-disc list-inside space-y-2 text-gray-300">
                  <li>Exclusive access to MCP events</li>
                  <li>Networking opportunities with like-minded music enthusiasts</li>
                  <li>Participate in workshops and masterclasses</li>
                  <li>Contribute to the growth of the electronic music scene</li>
                  <li>Be part of a supportive and inclusive community</li>
                </ul>
              </div>

              <div className="bg-mcp-orange/20 p-4 rounded-md flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 text-mcp-orange mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-300">
                  Membership is free of charge. However, please note that your request will be automatically rejected if
                  you are not following our Instagram account:
                  <a
                    href="https://www.instagram.com/musiconnectingpeople_"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold hover:underline text-mcp-orange"
                  >
                    {" "}
                    @musicconnectingpeople_
                  </a>
                </p>
              </div>

              {!isSubmitted ? (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label htmlFor="firstName" className="text-gray-300">
                        First Name
                      </Label>
                      <Input
                        id="firstName"
                        required
                        className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
                      />
                    </div>
                    <div>
                      <Label htmlFor="lastName" className="text-gray-300">
                        Last Name
                      </Label>
                      <Input
                        id="lastName"
                        required
                        className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="email" className="text-gray-300">
                      Email
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      required
                      className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
                    />
                  </div>
                  <div>
                    <Label htmlFor="instagram" className="text-gray-300">
                      Instagram Account
                    </Label>
                    <Input
                      id="instagram"
                      required
                      className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
                      placeholder="@yourusername"
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-mcp-gradient hover:opacity-90 text-white font-bold py-3 rounded-md transition-all duration-300 transform hover:scale-105"
                  >
                    Submit Application
                  </Button>
                </form>
              ) : (
                <div className="text-center space-y-4">
                  <p className="text-xl font-semibold gradient-text">Thank you for your application!</p>
                  <p className="text-gray-300">
                    Your request will be processed by the Music Connecting People team. We will be in touch soon.
                  </p>
                </div>
              )}
            </CardContent>
            <CardFooter className="text-sm text-gray-400 justify-center">
              <Link href="/" className="flex items-center hover:text-mcp-orange transition-colors">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Return to Home Page
              </Link>
            </CardFooter>
          </Card>
        </motion.div>
      </div>

      {/* Success Modal */}
      <Dialog open={isSuccessModalOpen} onOpenChange={setIsSuccessModalOpen}>
        <DialogContent className="bg-black border border-mcp-orange/50 text-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold gradient-text flex items-center">
              <CheckCircle className="w-6 h-6 mr-2 text-green-500" />
              Application Submitted Successfully
            </DialogTitle>
            <DialogDescription className="text-gray-300">
              Thank you for your interest in joining the Music Connecting People community. We have received your
              application and our team will review it shortly. You will receive an email with further information soon.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Button
              onClick={() => setIsSuccessModalOpen(false)}
              className="w-full bg-mcp-gradient hover:opacity-90 text-white transition-all duration-300"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Error Modal */}
      <Dialog open={isErrorModalOpen} onOpenChange={setIsErrorModalOpen}>
        <DialogContent className="bg-black border border-mcp-orange/50 text-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-red-500 flex items-center">
              <XCircle className="w-6 h-6 mr-2" />
              Error Submitting Application
            </DialogTitle>
            <DialogDescription className="text-gray-300">{errorMessage}</DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Button
              onClick={() => setIsErrorModalOpen(false)}
              className="w-full bg-mcp-gradient hover:opacity-90 text-white transition-all duration-300"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

