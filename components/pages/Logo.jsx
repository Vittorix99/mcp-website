import Image from "next/image"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"

export const LogoSection = () => {
  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  if (process.env.NEXT_PUBLIC_BRAND === "old") {
    return (
      <motion.div className="relative z-10 text-center px-4" initial="initial" animate="animate" variants={fadeInUp}>
        <h1 className="text-6xl md:text-8xl font-bold mb-3 gradient-text">MUSIC CONNECTING PEOPLE</h1>
        <motion.p className="text-xl md:text-2xl mb-8 text-gray-300" variants={fadeInUp}>
          Experience the rhythm. Connect with the community.
        </motion.p>
        <motion.div variants={fadeInUp}>
          <Button
            size="lg"
            className="bg-mcp-gradient hover:opacity-90 text-white font-bold py-3 px-6 rounded-md transition-all duration-300 transform hover:scale-105"
            onClick={() => {
              document.getElementById("join").scrollIntoView({ behavior: "smooth" })
            }}
          >
            Join Our Cultural Association
          </Button>
        </motion.div>
      </motion.div>
    )
  } else {
    return (
      <motion.div className="relative z-10 text-center px-4" initial="initial" animate="animate" variants={fadeInUp}>
        <motion.div variants={fadeInUp}>
          <Image src="/logonew.png" alt="MCP Logo" width={400} height={200} className="mx-auto invert brightness-0" />
        </motion.div>
        <motion.h2
          className="sr-only text-4xl md:text-5xl sm:text-4xl font-bold mb-4 gradient-text"
          variants={fadeInUp}
        >
          MUSIC CONNECTING PEOPLE
        </motion.h2>
        <motion.p className="text-xl md:text-2xl mt-5 mb-8 text-gray-300" variants={fadeInUp}>
          Experience the rhythm. Connect with the community.
        </motion.p>
        <motion.div variants={fadeInUp}>
          <Button
            size="lg"
            className="bg-mcp-gradient hover:opacity-90 text-white font-bold py-3 px-6 rounded-md transition-all duration-300 transform hover:scale-105"
            onClick={() => {
              document.getElementById("join").scrollIntoView({ behavior: "smooth" })
            }}
          >
            Join Our Community
          </Button>
        </motion.div>
      </motion.div>
    )
  }
}

