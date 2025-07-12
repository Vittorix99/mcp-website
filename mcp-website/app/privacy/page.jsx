"use client"

import { motion } from "framer-motion"
import Link from "next/link"

export default function PrivacyPolicy() {
  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  return (
    <div className="min-h-screen bg-black text-white py-12 md:py-24">
      <div className="container mx-auto px-4">
        <motion.h1
          className="text-3xl md:text-5xl font-bold text-center text-mcp-orange mb-6 md:mb-12"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          Privacy Policy
        </motion.h1>
        <motion.div
          className="space-y-4 md:space-y-6 max-w-3xl mx-auto text-sm md:text-base px-2 md:px-0"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          <p>
            Your privacy is important to us. It is Music Connecting People's policy to respect your privacy regarding
            any information we may collect from you across our website and other sites we own and operate.
          </p>

          <h2 className="text-xl md:text-2xl font-semibold text-mcp-orange mt-6 md:mt-8">1. Information We Collect</h2>
          <p>
            We only ask for personal information when we truly need it to provide a service to you. We collect it by
            fair and lawful means, with your knowledge and consent. We also let you know why we're collecting it and how
            it will be used.
          </p>

          <h2 className="text-xl md:text-2xl font-semibold text-mcp-orange mt-6 md:mt-8">2. Use of Information</h2>
          <p>
            We only retain collected information for as long as necessary to provide you with your requested service.
            What data we store, we'll protect within commercially acceptable means to prevent loss and theft, as well as
            unauthorized access, disclosure, copying, use or modification.
          </p>

          <h2 className="text-xl md:text-2xl font-semibold text-mcp-orange mt-6 md:mt-8">3. Sharing of Information</h2>
          <p>
            We don't share any personally identifying information publicly or with third-parties, except when required
            to by law.
          </p>

          <h2 className="text-xl md:text-2xl font-semibold text-mcp-orange mt-6 md:mt-8">4. Your Rights</h2>
          <p>
            You are free to refuse our request for your personal information, with the understanding that we may be
            unable to provide you with some of your desired services.
          </p>

          <p className="mt-8 md:mt-12 text-center text-xs md:text-sm">
            If you have any questions about how we handle user data and personal information, feel free to contact us at{" "}
            <Link href="mailto:privacy@musicconnectingpeople.com" className="text-mcp-orange hover:underline">
              privacy@musicconnectingpeople.com
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

