
export const AnimatedBackground = () => (
    <div className="fixed inset-0 z-0 opacity-20">
      <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="lines" width="100" height="100" patternUnits="userSpaceOnUse">
            <path d="M0,50 Q25,25 50,50 T100,50" fill="none" stroke="rgba(249, 115, 22, 0.5)" strokeWidth="2">
              <animate attributeName="d" from="M0,50 Q25,0 50,50 T100,50" to="M0,50 Q25,100 50,50 T100,50" dur="10s" repeatCount="indefinite" />
            </path>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#lines)" />
      </svg>
    </div>
  )

  export default AnimatedBackground;