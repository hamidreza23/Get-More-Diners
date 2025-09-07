interface IconProps {
  name: string
  className?: string
}

export function Icon({ name, className = "text-2xl" }: IconProps) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>
}
