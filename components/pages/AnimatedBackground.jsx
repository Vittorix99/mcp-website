"use client";
import React, { useState, useEffect } from "react";
import clsx from "clsx"; // Libreria per gestire classi condizionali (opzionale)

export const AnimatedBackground = () => {
  const [isSmallScreen, setIsSmallScreen] = useState(false);

  useEffect(() => {
    // Controlla la dimensione dello schermo solo lato client
    const checkScreenSize = () => {
      setIsSmallScreen(window.matchMedia("(max-width: 640px)").matches);
    };

    checkScreenSize(); // Controllo iniziale

    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  return (
    <div className={clsx("fixed inset-0 z-0 pointer-events-none overflow-hidden", { "mb-12": isSmallScreen })}>
      <svg
        className="w-full h-full opacity-40"
        xmlns="http://www.w3.org/2000/svg"
        viewBox={isSmallScreen ? "0 0 1260 600" : "0 0 1440 300"} // Cambia il viewBox per schermi piccoli
        style={{ willChange: "transform" }} // Ottimizzazione per Safari
      >
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#FF6B00" />
            <stop offset="100%" stopColor="#FF0000" />
          </linearGradient>
        </defs>

        {/* Prima onda */}
        <g>
          <path
            fill="none"
            stroke="url(#gradient)"
            strokeWidth={isSmallScreen ? 8 : 3}
            strokeOpacity={isSmallScreen ? 0.8 : 0.6}
            d={isSmallScreen 
              ? "M0,200 C320,360,420,360,740,200 C1060,80,1360,80,1440,200"
              : "M0,160 C320,300,420,300,740,160 C1060,20,1360,20,1440,160"
            }
          >
            <animate
              attributeName="d"
              dur="40s"
              repeatCount="indefinite"
              values={isSmallScreen
                ? `M0,200 C320,360,420,360,740,200 C1060,80,1360,80,1440,200;
                   M0,200 C320,80,420,80,740,200 C1060,360,1360,360,1440,200;
                   M0,200 C320,360,420,360,740,200 C1060,80,1360,80,1440,200`
                : `M0,160 C320,300,420,300,740,160 C1060,20,1360,20,1440,160;
                   M0,160 C320,20,420,20,740,160 C1060,300,1360,300,1440,160;
                   M0,160 C320,300,420,300,740,160 C1060,20,1360,20,1440,160`
              }
            />
          </path>
        </g>

        {/* Seconda onda */}
        <g >
          <path
            fill="none"
            stroke="url(#gradient)"
            strokeWidth={isSmallScreen ? 8 : 2.5}
            strokeOpacity={isSmallScreen ? 0.8 : 0.5}
            d={isSmallScreen 
              ? "M0,140 C240,300,480,140,720,140 C960,140,1200,300,1440,140"
              : "M0,100 C240,200,480,100,720,100 C960,100,1200,200,1440,100"
            }
          >
            <animate
              attributeName="d"
              dur="40s"
              repeatCount="indefinite"
              values={isSmallScreen
                ? `M0,140 C240,300,480,140,720,140 C960,140,1200,300,1440,140;
                   M0,140 C240,60,480,280,720,140 C960,60,1200,280,1440,140;
                   M0,140 C240,300,480,140,720,140 C960,140,1200,300,1440,140`
                : `M0,100 C240,200,480,100,720,100 C960,100,1200,200,1440,100;
                   M0,100 C240,0,480,200,720,100 C960,0,1200,200,1440,100;
                   M0,100 C240,200,480,100,720,100 C960,100,1200,200,1440,100`
              }
            />
          </path>
        </g>

        {/* Terza onda */}
        <g>
          <path
            fill="none"
            stroke="url(#gradient)"
            strokeWidth={isSmallScreen ? 8 : 2.5}
            strokeOpacity={isSmallScreen ? 0.8 : 0.6}
            d={isSmallScreen 
              ? "M0,80 C180,160,360,40,540,80 C720,160,900,40,1080,80 C1260,160,1440,40,1440,80"
              : "M0,60 C180,90,360,30,540,60 C720,90,900,30,1080,60 C1260,90,1440,30,1440,60"
            }
          >
            <animate
              attributeName="d"
              dur="35s"
              repeatCount="indefinite"
              values={isSmallScreen
                ? `M0,80 C180,160,360,40,540,80 C720,160,900,40,1080,80 C1260,160,1440,40,1440,80;
                   M0,80 C180,40,360,160,540,80 C720,40,900,160,1080,80 C1260,40,1440,160,1440,80;
                   M0,80 C180,160,360,40,540,80 C720,160,900,40,1080,80 C1260,160,1440,40,1440,80`
                : `M0,60 C180,100,360,20,540,60 C720,100,900,20,1080,60 C1260,100,1440,20,1440,60;
                   M0,60 C180,20,360,100,540,60 C720,20,900,100,1080,60 C1260,20,1440,100,1440,60;
                   M0,60 C180,100,360,20,540,60 C720,100,900,20,1080,60 C1260,100,1440,20,1440,60`
              }
            />
          </path>
        </g>
      </svg>
    </div>
  );
};

export default AnimatedBackground;