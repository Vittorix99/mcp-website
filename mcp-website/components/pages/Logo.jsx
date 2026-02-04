"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export const LogoSection = () => {
  const router = useRouter();

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  };

  return (
    <motion.div
      className="relative z-10 text-center px-4"
      initial="initial"
      animate="animate"
      variants={fadeInUp}
    >
      <motion.div variants={fadeInUp}>
        <Image
          src="/logonew.png"
          alt="MCP Logo"
          width={400}
          height={200}
          className="mx-auto invert brightness-0 w-[280px] md:w-[400px]"
        />
      </motion.div>

      <motion.h2
        className="sr-only font-atlantico text-4xl md:text-5xl sm:text-4xl font-bold mb-4 gradient-text"
        variants={fadeInUp}
      >
        MUSIC CONNECTING PEOPLE
      </motion.h2>

      <motion.p
        className="font-helvetica text-xl md:text-2xl mt-4 md:mt-5 mb-6 md:mb-8 text-gray-300 max-w-xs md:max-w-none mx-auto"
        variants={fadeInUp}
      >
        Experience the rhythm. <br className="md:hidden" />
        Connect with the community.
      </motion.p>

    </motion.div>
  );
};
