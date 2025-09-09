'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { GetMoreDinersLogo } from '@/components/logos/get-more-diners-logo'
import { api } from '@/lib/api'
import {
  Search,
  PenTool,
  BarChart3,
  User,
  Menu,
  X,
  Plus,
  Settings,
  CreditCard,
  LogOut,
  Image as ImageIcon
} from 'lucide-react'

interface AppNavProps {
  className?: string
}

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  description: string
}

const navItems: NavItem[] = [
  {
    name: 'Search',
    href: '/app/search',
    icon: Search,
    description: 'Find and filter customers'
  },
  {
    name: 'Compose',
    href: '/app/compose',
    icon: PenTool,
    description: 'Create AI-powered campaigns'
  },
  {
    name: 'Campaigns',
    href: '/app/campaigns',
    icon: BarChart3,
    description: 'View campaign performance'
  },
  {
    name: 'AI Food Studio',
    href: '/app/ai/food-studio',
    icon: ImageIcon,
    description: 'Generate dish images (demo)'
  },
  {
    name: 'Profile',
    href: '/app/profile',
    icon: User,
    description: 'Restaurant settings'
  }
]

export function AppNav({ className }: AppNavProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [restaurant, setRestaurant] = useState<any>(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  // Create client only when needed to avoid SSR-time initialization

  useEffect(() => {
    const getUser = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
      return user
    }

    const getRestaurant = async () => {
      try {
        // Check if we have a valid session before making the API call
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()
        if (!session?.access_token) {
          console.log('No valid session, skipping restaurant data fetch')
          setRestaurant(null)
          return
        }
        
        const restaurantData = await api.getRestaurant()
        setRestaurant(restaurantData)
      } catch (error) {
        // Restaurant data might not be available yet, that's okay
        console.log('Restaurant data not available yet:', error)
        setRestaurant(null)
      }
    }

    const initializeData = async () => {
      const user = await getUser()
      if (user) {
        getRestaurant()
      }
    }

    initializeData()

    const supabase = createClient()
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null)
        if (event === 'SIGNED_OUT') {
          router.push('/signin')
        } else if (event === 'SIGNED_IN' && session) {
          getRestaurant()
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [router, supabase.auth])

  const handleSignOut = async () => {
    const supabase = createClient()
    try {
      await supabase.auth.signOut()
      toast.success('Signed out successfully')
      router.push('/')
    } catch (error) {
      toast.error('Error signing out')
    }
  }

  const getUserInitial = () => {
    return user?.email?.charAt(0).toUpperCase() || 'U'
  }

  const getUserDisplayName = () => {
    return user?.user_metadata?.full_name || user?.email || 'User'
  }

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false)
  }

  return (
    <header className={cn("border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50", className)}>
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo and Desktop Nav */}
        <div className="flex items-center space-x-8">
          <Link 
            href="/app" 
            className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-md"
            aria-label="Get More Diners Home"
          >
            <GetMoreDinersLogo />
            <span className="text-xl font-bold brand-text-gradient">
              Get More Diners
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-1" role="navigation" aria-label="Main navigation">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href || (item.href !== '/app' && pathname.startsWith(item.href))
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                    isActive
                      ? "text-primary bg-primary/10"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                  aria-current={isActive ? 'page' : undefined}
                  title={item.description}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Desktop Actions and User Menu */}
        <div className="flex items-center space-x-4">
          {/* New Campaign Button - Desktop */}
          <Button
            asChild
            className="terracotta-button hidden md:inline-flex"
            size="sm"
          >
            <Link href="/app/compose" aria-label="Create new campaign">
              <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
              New Campaign
            </Link>
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                className="relative h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 p-0"
                aria-label={`User menu for ${getUserDisplayName()}`}
              >
                <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center border border-primary/20">
                  <User className="h-5 w-5 text-primary" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <div className="flex items-center gap-3">
                    {restaurant?.logo_url ? (
                      <img 
                        src={restaurant.logo_url} 
                        alt={restaurant.name || 'Restaurant Logo'} 
                        className="h-8 w-8 rounded-full object-cover"
                      />
                    ) : (
                      <GetMoreDinersLogo />
                    )}
                    <div className="flex flex-col">
                      <p className="text-sm font-medium leading-none">
                        {restaurant?.name || getUserDisplayName()}
                      </p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user?.email}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary" className="text-xs">
                      Free Plan
                    </Badge>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/app/profile" className="flex items-center">
                  <User className="h-4 w-4 mr-2" aria-hidden="true" />
                  Restaurant Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem disabled>
                <Settings className="h-4 w-4 mr-2" aria-hidden="true" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuItem disabled>
                <CreditCard className="h-4 w-4 mr-2" aria-hidden="true" />
                Billing
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleSignOut}>
                <LogOut className="h-4 w-4 mr-2" aria-hidden="true" />
                Sign Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-menu"
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
          </Button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <div 
          id="mobile-menu"
          className="lg:hidden border-t bg-background/95 backdrop-blur"
          role="navigation"
          aria-label="Mobile navigation"
        >
          <div className="container mx-auto px-4 py-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href || (item.href !== '/app' && pathname.startsWith(item.href))
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={closeMobileMenu}
                  className={cn(
                    "flex items-center space-x-3 px-3 py-3 rounded-md text-sm font-medium transition-colors w-full",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                    isActive
                      ? "text-primary bg-primary/10"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                  <div>
                    <div>{item.name}</div>
                    <div className="text-xs text-muted-foreground">{item.description}</div>
                  </div>
                </Link>
              )
            })}
            
            {/* Mobile New Campaign Button */}
            <div className="pt-2 mt-2 border-t">
              <Button
                asChild
                className="terracotta-button w-full"
                onClick={closeMobileMenu}
              >
                <Link href="/app/compose">
                  <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
                  Create New Campaign
                </Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
