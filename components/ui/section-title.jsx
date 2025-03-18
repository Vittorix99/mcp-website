export function SectionTitle({ children, className = "", as = "h2" }) {
    const Component = as
  
    return (
      <Component className={`font-atlantico text-5xl md:text-5xl font-bold mb-8 gradient-text text-center ${className}`}>
        {children}
      </Component>
    )
  }
  
  