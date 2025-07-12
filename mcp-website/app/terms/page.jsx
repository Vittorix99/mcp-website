"use client"

import { motion } from "framer-motion"
import Link from "next/link"

export default function TermsOfService() {
  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  return (
    <div className="min-h-screen bg-black text-white py-24">
      <div className="container mx-auto px-4">
        <motion.h1
          className="text-4xl md:text-5xl font-bold text-center text-mcp-orange mb-12"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          Terms of Service
        </motion.h1>
        <motion.div className="space-y-6 max-w-3xl mx-auto" initial="initial" animate="animate" variants={fadeInUp}>
          <p>
            Welcome to Music Connecting People. By using our services, you agree to these terms. Please read them
            carefully.
          </p>

          <h2 className="text-2xl font-semibold text-mcp-orange mt-8">1. Use of Service</h2>
          <p>
            You must follow any policies made available to you within the Services. Don't misuse our Services. For
            example, don't interfere with our Services or try to access them using a method other than the interface and
            the instructions that we provide.
          </p>

          <h2 className="text-2xl font-semibold text-mcp-orange mt-8">2. Privacy</h2>
          <p>
            MCP's privacy policies explain how we treat your personal data and protect your privacy when you use our
            Services. By using our Services, you agree that MCP can use such data in accordance with our privacy
            policies.
          </p>

          <h2 className="text-2xl font-semibold text-mcp-orange mt-8">3. Modifications</h2>
          <p>
            We may modify these terms or any additional terms that apply to a Service to, for example, reflect changes
            to the law or changes to our Services. You should look at the terms regularly.
          </p>

          <h2 className="text-2xl font-semibold text-mcp-orange mt-8">4. Liability</h2>
          <p>
            When permitted by law, MCP and its suppliers and distributors will not be responsible for lost profits,
            revenues, or data, financial losses or indirect, special, consequential, exemplary, or punitive damages.
          </p>

          <p className="mt-12 text-center">
            For more information, please contact us at{" "}
            <Link href="mailto:info@musicconnectingpeople.com" className="text-mcp-orange hover:underline">
              info@musicconnectingpeople.com
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

