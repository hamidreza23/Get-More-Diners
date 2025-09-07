"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Icon } from "@/components/ui/icon"

interface MobileMenuProps {
  isOpen: boolean
  onToggle: () => void
}

export function MobileMenu({ isOpen, onToggle }: MobileMenuProps) {
  if (!isOpen) return null

  return (
    <div className="lg:hidden">
      <div className="fixed inset-0 z-50 bg-black bg-opacity-50" onClick={onToggle} />
      <div className="fixed right-0 top-0 z-50 h-full w-64 bg-white shadow-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold text-gray-800">Menu</h3>
          <button onClick={onToggle} className="p-2 text-gray-600 hover:text-gray-800">
            <Icon name="close" className="text-2xl" />
          </button>
        </div>
        <nav className="p-4 space-y-4">
          <Link
            href="#features"
            className="block text-gray-600 hover:text-[var(--primary-color)] transition-colors duration-300 font-medium py-2"
            onClick={onToggle}
          >
            Features
          </Link>
          <Link
            href="#pricing"
            className="block text-gray-600 hover:text-[var(--primary-color)] transition-colors duration-300 font-medium py-2"
            onClick={onToggle}
          >
            Pricing
          </Link>
          <Link
            href="#about"
            className="block text-gray-600 hover:text-[var(--primary-color)] transition-colors duration-300 font-medium py-2"
            onClick={onToggle}
          >
            About Us
          </Link>
          <div className="pt-4 space-y-2">
            <Button variant="ghost" className="w-full text-gray-800 hover:bg-gray-100" onClick={onToggle}>
              Request a Demo
            </Button>
            <Link href="/signin" onClick={onToggle}>
              <Button variant="ghost" className="w-full text-gray-800 hover:bg-gray-100">
                Sign In
              </Button>
            </Link>
            <Link href="/signup" onClick={onToggle}>
              <Button className="w-full bg-[var(--primary-color)] hover:bg-[var(--primary-color)]/90 text-white">
                Sign Up Free
              </Button>
            </Link>
          </div>
        </nav>
      </div>
    </div>
  )
}

