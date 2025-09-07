interface DineBoostLogoProps {
  className?: string
}

export function DineBoostLogo({ className = "h-8 w-8" }: DineBoostLogoProps) {
  return (
    <svg
      className={`${className} text-[var(--primary-color)]`}
      fill="none"
      viewBox="0 0 48 48"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M4 4H17.3334V17.3334H30.6666V30.6666H44V44H4V4Z" fill="currentColor"></path>
    </svg>
  )
}

