"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ContactUs } from "@/components/pages/ContactUs";
import { LogoSection } from "@/components/pages/Logo";
import { NextEventSection } from "@/components/pages/NextEventSection";
import { AboutUs } from "@/components/pages/AboutUs";
import { getNextEvent } from "@/services/events";
import { Footer } from "@/components/Footer";
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider";
import { SectionTitle } from "@/components/ui/section-title";

export default function LandingPage() {
  const [nextEvent, setNextEvent] = useState(null);
  const [hasNextEvent, setHasNextEvent] = useState(false);

  const isMembershipActive = process.env.NEXT_PUBLIC_MEMBERSHIP_PAGE_ACTIVE === "true";

  useEffect(() => {
    const fetchNextEvent = async () => {
      try {
        const { success, event } = await getNextEvent();
        if (success && event) {
          setNextEvent(event);
          setHasNextEvent(true);
        } else {
          setHasNextEvent(false);
        }
      } catch (err) {
        console.error("Error fetching next event:", err);
        setHasNextEvent(false);
      }
    };

    fetchNextEvent();
  }, []);

  return (
    <div className="min-h-screen font-helvetica">
      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center">
        <LogoSection />
      </section>

      <AnimatedSectionDivider color="ORANGE" />

      {/* Next Event Section */}
      {hasNextEvent && (
        <>
          <section className="py-12 md:py-24 relative">
            <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-mcp-orange/5 to-black/0" />
            <NextEventSection event={nextEvent} />
          </section>
          <AnimatedSectionDivider color="RED" />
        </>
      )}

      {/* About Section */}
      <section id="about" className="relative py-12 md:py-24">
        <AboutUs />
      </section>

      <AnimatedSectionDivider color="ORANGE" />

      {/* Join Us Section */}
      {isMembershipActive && (
        <>
        <section id="join" className="relative py-12 md:py-24">
          <div className="container mx-auto px-4 text-center">
            <SectionTitle as="h1" className="mt-3 md:mt-8 text-3xl md:text-5xl">
              Join Our Community
            </SectionTitle>
            <p className="font-helvetica text-sm md:text-lg mb-6 md:mb-8 text-gray-300 max-w-2xl mx-auto px-3">
              Become a part of our movement and experience the power of music connection.
            </p>
            <Link href="/subscribe">
              <Button
                size="default"
                className="tracking-wider bg-mcp-gradient hover:opacity-90 text-white border-0 text-sm md:text-base h-10 md:h-12 px-4 md:px-6"
              >
                Sign Up Now
              </Button>
            </Link>
          </div>
        </section>
         <AnimatedSectionDivider color="RED" />

          </>
        

      )}

     
     

      {/* Contact Section */}
      <section id="contact-section" className="relative py-12 md:py-24">
        <ContactUs />
      </section>

      {/* Footer */}
    </div>
  );
}