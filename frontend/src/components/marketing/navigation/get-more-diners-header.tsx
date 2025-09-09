"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase"
import { GetMoreDinersLogo } from "@/components/marketing/logos/get-more-diners-logo"
import { Icon } from "@/components/ui/icon"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

interface GetMoreDinersHeaderProps {
  currentPage?: string
}

export function GetMoreDinersHeader({ currentPage }: GetMoreDinersHeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const router = useRouter()

  const navItems = [
    { href: "/app", label: "Dashboard" },
    { href: "/app/search", label: "Search" },
    { href: "/app/campaigns", label: "Campaigns" },
    { href: "/app/compose", label: "Compose" },
    { href: "/app/profile", label: "Profile" },
  ]

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const handleLogout = async () => {
    const supabase = createClient()
    try {
      await supabase.auth.signOut()
      toast.success('Successfully signed out')
      router.push('/')
    } catch (error) {
      console.error('Logout error:', error)
      toast.error('Failed to sign out')
    }
  }

  return (
    <>
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <GetMoreDinersLogo />
              </div>
              <h1 className="text-xl font-bold text-[#1a1a1a]">Get More Diners</h1>
            </div>
            <nav className="hidden md:flex items-center gap-8">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`text-sm font-medium transition-colors ${
                    currentPage === item.label ? "text-primary-brand font-bold" : "text-[#666666] hover:text-primary-brand"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="flex items-center gap-4">
              <button className="relative rounded-full p-2 text-[#666666] hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-brand">
                <Icon name="notifications" />
              </button>
              <div
                className="h-10 w-10 rounded-full bg-cover bg-center"
                style={{
                  backgroundImage: 'url("/professional-profile-avatar.png")',
                }}
              ></div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="hidden md:flex text-[#666666] hover:text-red-600 hover:bg-red-50"
              >
                <Icon name="logout" className="mr-2" />
                Logout
              </Button>
              <button className="md:hidden" onClick={toggleMobileMenu}>
                <Icon name="menu" className="text-2xl text-[#666666]" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {isMobileMenuOpen && (
        <div className="md:hidden">
          <div className="fixed inset-0 z-50 bg-black bg-opacity-50" onClick={toggleMobileMenu} />
          <div className="fixed right-0 top-0 z-50 h-full w-64 bg-white shadow-lg">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-[#1a1a1a]">Menu</h3>
              <button onClick={toggleMobileMenu} className="p-2 text-[#666666] hover:text-[#1a1a1a]">
                <Icon name="close" />
              </button>
            </div>
            <nav className="p-4 space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block py-2 transition-colors ${
                    currentPage === item.label ? "text-primary-brand font-bold" : "text-[#666666] hover:text-primary-brand"
                  }`}
                  onClick={toggleMobileMenu}
                >
                  {item.label}
                </Link>
              ))}
              <div className="pt-4 border-t border-gray-200">
                <Button
                  variant="ghost"
                  onClick={() => {
                    handleLogout()
                    toggleMobileMenu()
                  }}
                  className="w-full justify-start text-[#666666] hover:text-red-600 hover:bg-red-50"
                >
                  <Icon name="logout" className="mr-2" />
                  Logout
                </Button>
              </div>
            </nav>
          </div>
        </div>
      )}
    </>
  )
}
