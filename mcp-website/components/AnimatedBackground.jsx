"use client"

import React from "react"
import clsx from "clsx"
import { useIsMobile } from "@/hooks/use-mobile"

export const AnimatedBackground = () => {
  const isMobile = useIsMobile()

  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      <svg
        className="w-full h-full opacity-40"
        xmlns="http://www.w3.org/2000/svg"
        viewBox={isMobile ? "0 0 600 1440" : "0 0 1440 300"}
        style={{ willChange: "transform" }}
      >
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2={isMobile ? "0%" : "100%"} y2={isMobile ? "100%" : "0%"}>
            <stop offset="0%" stopColor="#FF6B00" />
            <stop offset="100%" stopColor="#FF0000" />
          </linearGradient>
        </defs>

        {/* Mobile: onde centrate e distanziate */}
        <g transform={isMobile ? "translate(100)" : undefined}>
          {/* Onda 1 */}
          <path
            fill="none"
            stroke="url(#gradient)"
            strokeWidth={isMobile ? 6 : 3}
            strokeOpacity={isMobile ? 0.7 : 0.6}
            d={
              isMobile
                ? "M0,0 C80,320,80,720,0,1040 C-80,1260,-80,1440,0,1440"
                : "M0,160 C320,300,420,300,740,160 C1060,20,1360,20,1440,160"
            }
          >
            <animate
              attributeName="d"
              dur="40s"
              repeatCount="indefinite"
              values={
                isMobile
                  ? `M0,0 C80,320,80,720,0,1040 C-80,1260,-80,1440,0,1440;
                     M0,0 C-80,320,-80,720,0,1040 C80,1260,80,1440,0,1440;
                     M0,0 C80,320,80,720,0,1040 C-80,1260,-80,1440,0,1440`
                  : `M0,160 C320,300,420,300,740,160 C1060,20,1360,20,1440,160;
                     M0,160 C320,20,420,20,740,160 C1060,300,1360,300,1440,160;
                     M0,160 C320,300,420,300,740,160 C1060,20,1360,20,1440,160`
              }
            />
          </path>
        </g>

        <g transform={isMobile ? "translate(300)" : undefined}>
          {/* Onda 2 */}
          <path
            fill="none"
            stroke="url(#gradient)"
            strokeWidth={isMobile ? 6 : 2.5}
            strokeOpacity={isMobile ? 0.6 : 0.5}
            d={
              isMobile
                ? "M0,0 C100,360,0,720,0,1080 C0,1260,100,1440,0,1440"
                : "M0,100 C240,200,480,100,720,100 C960,100,1200,200,1440,100"
            }
          >
            <animate
              attributeName="d"
              dur="40s"
              repeatCount="indefinite"
              values={
                isMobile
                  ? `M0,0 C100,360,0,720,0,1080 C0,1260,100,1440,0,1440;
                     M0,0 C0,360,100,720,0,1080 C0,1260,100,1440,0,1440;
                     M0,0 C100,360,0,720,0,1080 C0,1260,100,1440,0,1440`
                  : `M0,100 C240,200,480,100,720,100 C960,100,1200,200,1440,100;
                     M0,100 C240,0,480,200,720,100 C960,0,1200,200,1440,100;
                     M0,100 C240,200,480,100,720,100 C960,100,1200,200,1440,100`
              }
            />
          </path>
        </g>

        <g transform={isMobile ? "translate(440)" : undefined}>
          {/* Onda 3 */}
          <path
            fill="none"
            stroke="url(#gradient)"
            strokeWidth={isMobile ? 6 : 2.5}
            strokeOpacity={isMobile ? 0.6 : 0.6}
            d={
              isMobile
                ? "M0,0 C120,240,0,720,0,1080 C0,1320,120,1440,0,1440"
                : "M0,60 C180,90,360,30,540,60 C720,90,900,30,1080,60 C1260,90,1440,30,1440,60"
            }
          >
            <animate
              attributeName="d"
              dur="35s"
              repeatCount="indefinite"
              values={
                isMobile
                  ? `M0,0 C120,240,0,720,0,1080 C0,1320,120,1440,0,1440;
                     M0,0 C0,240,120,720,0,1080 C0,1320,120,1440,0,1440;
                     M0,0 C120,240,0,720,0,1080 C0,1320,120,1440,0,1440`
                  : `M0,60 C180,100,360,20,540,60 C720,100,900,20,1080,60 C1260,100,1440,20,1440,60;
                     M0,60 C180,20,360,100,540,60 C720,20,900,100,1080,60 C1260,20,1440,100,1440,60;
                     M0,60 C180,100,360,20,540,60 C720,100,900,20,1080,60 C1260,100,1440,20,1440,60`
              }
            />
          </path>
        </g>
      </svg>
    </div>
  )
}

export default AnimatedBackground