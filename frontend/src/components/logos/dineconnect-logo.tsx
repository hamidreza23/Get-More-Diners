interface DineConnectLogoProps {
  className?: string
}

export function DineConnectLogo({ className = "h-8 w-8" }: DineConnectLogoProps) {
  return (
    <svg className={`${className} text-[#ea2a33]`} fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <g clipPath="url(#clip0_6_330)">
        <path
          clipRule="evenodd"
          d="M24 0.757355L47.2426 24L24 47.2426L0.757355 24L24 0.757355ZM21 35.7574V12.2426L9.24264 24L21 35.7574Z"
          fill="currentColor"
          fillRule="evenodd"
        ></path>
      </g>
      <defs>
        <clipPath id="clip0_6_330">
          <rect fill="white" height="48" width="48"></rect>
        </clipPath>
      </defs>
    </svg>
  )
}
