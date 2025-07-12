"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";
import { useRouter } from "next/navigation";

export const LogoSection = () => {
  const router = useRouter();
  const isMembershipActive = process.env.NEXT_PUBLIC_MEMBERSHIP_PAGE_ACTIVE === "true";

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

      {isMembershipActive && (
        <motion.div variants={fadeInUp}>
          <Button
            size="lg"
            className="tracking-wider bg-mcp-gradient hover:opacity-90 text-white border-0 text-sm md:text-base h-10 md:h-12"
            onClick={() => {
              router.push(routes.subscribe);
            }}
          >
            Join Our Community
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
};