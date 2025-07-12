export function SectionTitle({ children, className = "", as = "h2" }) {
  const Component = as

  return (
    <Component
      className={`font-atlantico text-4xl md:text-5xl font-bold mb-4 md:mb-8 gradient-text text-center tracking-atlantico-wide md:tracking-atlantico-wider ${className}`}
    >
      {children}
    </Component>
  )
}

