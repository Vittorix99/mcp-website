
import React from 'react';
import Image from 'next/image';
import { Button } from "@/components/ui/button"




export const LogoSection = () => {
    if (process.env.NEXT_PUBLIC_BRAND==='old')  {

        return (
            <div className="relative z-10 text-center px-4">
            <h1 className="text-6xl md:text-8xl font-bold mb-6 text-orange-500">
              MUSIC CONNECTING PEOPLE
            </h1>
            <p className="text-xl md:text-2xl mb-8">
              Experience the rhythm. Connect with the community.
            </p>
            <Button 
              size="lg" 
              className="bg-orange-500 hover:bg-orange-600 text-black"
              onClick={() => {
                document.getElementById('join').scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Join Our Cultural Association
            </Button>
          </div>
        )
    }
    else {
        return (
            <div className="relative z-10 text-center px-4">
            <Image 
              src="/logonew.png" 
              alt="MCP Logo" 
              width={400} 
              height={200} 
              className="mx-auto  invert brightness-0"
              />
                       <h2 className="text-4xl  md:text-5xl sm:text-4xl font-bold mb-4 text-orange-500">
              MUSIC CONNECTING PEOPLE
            </h2>
            <p className="text-xl md:text-2xl mb-8">
              Experience the rhythm. Connect with the community.
            </p>
            <Button 
              size="lg" 
              className="bg-orange-500 hover:bg-orange-600 text-black"
              onClick={() => {
                document.getElementById('join').scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Join Our Community
            </Button>
          </div>
        )
    }
}
