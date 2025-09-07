"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { GetMoreDinersLogo } from "@/components/marketing/logos/get-more-diners-logo"
import { MobileMenu } from "@/components/marketing/navigation/mobile-menu"
import { Icon } from "@/components/ui/icon"

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  return (
    <>
      <header className="flex items-center justify-between whitespace-nowrap px-10 py-5">
        <div className="flex items-center gap-3 text-gray-800">
          <GetMoreDinersLogo />
          <h2 className="text-gray-800 text-2xl font-bold leading-tight tracking-[-0.015em]">Get More Diners</h2>
        </div>
        <div className="hidden lg:flex items-center gap-8 text-lg">
          <Link
            href="#features"
            className="text-gray-600 hover:text-primary-brand transition-colors duration-300 font-medium leading-normal"
          >
            Features
          </Link>
          <Link
            href="#pricing"
            className="text-gray-600 hover:text-primary-brand transition-colors duration-300 font-medium leading-normal"
          >
            Pricing
          </Link>
          <Link
            href="#about"
            className="text-gray-600 hover:text-primary-brand transition-colors duration-300 font-medium leading-normal"
          >
            About Us
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="ghost" className="hidden lg:flex text-gray-800 hover:bg-gray-100">
            Request a Demo
          </Button>
          <Link href="/signin" className="hidden lg:flex">
            <Button variant="ghost" className="text-gray-800 hover:bg-gray-100">Sign In</Button>
          </Link>
          <Link href="/signup">
            <Button className="bg-primary-brand hover:bg-primary-brand/90 text-white">Sign Up Free</Button>
          </Link>
          <button className="lg:hidden" onClick={toggleMobileMenu}>
            <Icon name="menu" className="text-4xl text-gray-800" />
          </button>
        </div>
      </header>
      <MobileMenu isOpen={isMobileMenuOpen} onToggle={toggleMobileMenu} />
    </>
  )
}

