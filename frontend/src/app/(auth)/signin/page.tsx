'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import { api } from '@/lib/api'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GetMoreDinersLogo } from "@/components/marketing/logos/get-more-diners-logo"
import { toast } from 'sonner'

export default function SignInPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [infoMsg, setInfoMsg] = useState<string | null>(null)
  const [resending, setResending] = useState(false)

  // Check if user is already authenticated and redirect if so
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = createClient()
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.access_token) {
          // User is already authenticated, redirect to dashboard
          router.push('/app')
        }
      } catch (error) {
        // Ignore errors, let user stay on signin page
        console.log('[SignIn] Auth check error:', error)
      }
    }
    checkAuth()
  }, [])

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrorMsg(null)
    setInfoMsg(null)

    try {
      const supabase = createClient()
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        const msg = (error as any)?.message || 'Invalid credentials'
        // Friendlier guidance
        if (/invalid/i.test(msg)) {
          setErrorMsg('Invalid email or password. If you never set a password, use Forgot password to create one.')
        } else if (/confirm|verified/i.test(msg)) {
          setErrorMsg('Your email is not confirmed yet. Please check your inbox or resend confirmation below.')
        } else {
          setErrorMsg(msg)
        }
        toast.error('Sign-in failed')
      } else {
        toast.success('Successfully signed in!')
        router.push('/app')
      }
    } catch (error) {
      setErrorMsg('An unexpected error occurred')
      toast.error('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  // Magic Link removed per product decision – password-based sign-in only

  const handleResendConfirmation = async () => {
    setResending(true)
    setErrorMsg(null)
    setInfoMsg(null)
    try {
      const supabase = createClient()
      // Resend signup confirmation email if user registered but not confirmed
      const { error } = await supabase.auth.resend({
        type: 'signup',
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback?next=/app`,
        },
      })
      if (error) {
        setErrorMsg(error.message)
        toast.error(error.message)
      } else {
        setInfoMsg('Confirmation email resent. Please check your inbox.')
        toast.success('Confirmation email resent')
      }
    } catch (e) {
      setErrorMsg('Failed to resend confirmation email')
      toast.error('Failed to resend confirmation email')
    } finally {
      setResending(false)
    }
  }

  const handleForgotPassword = async (e: React.MouseEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setInfoMsg(null)
    if (!email) {
      setErrorMsg('Please enter your email above, then click Forgot password.')
      return
    }
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
      })
      if (error) {
        setErrorMsg(error.message)
        toast.error(error.message)
      } else {
        setInfoMsg('We sent a password reset link to your email.')
        toast.success('Password reset email sent')
      }
    } catch (e) {
      setErrorMsg('Failed to send password reset email')
    }
  }
  return (
    <div className="min-h-screen bg-white text-gray-900 flex items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center">
            <GetMoreDinersLogo />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Sign in to Get More Diners</h1>
          <p className="mt-2 text-base text-gray-600">Enter your details below to access your account.</p>
        </div>

        <form onSubmit={handleSignIn} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="text-gray-900 placeholder-gray-400 focus:border-primary-brand focus:ring-primary-brand"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <Label htmlFor="password">Password</Label>
              <a href="#" onClick={handleForgotPassword} className="text-sm font-medium text-primary-brand hover:text-primary-brand/80">
                Forgot password?
              </a>
            </div>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="text-gray-900 placeholder-gray-400 focus:border-primary-brand focus:ring-primary-brand"
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="flex w-full justify-center rounded-md bg-primary-brand px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-brand/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-brand"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        {(errorMsg || infoMsg) && (
          <div className="rounded-md border p-3 text-sm mt-2">
            {errorMsg && <p className="text-red-600">{errorMsg}</p>}
            {infoMsg && <p className="text-slate-700">{infoMsg}</p>}
            {errorMsg && /confirm|verified/i.test(errorMsg) && (
              <div className="mt-2">
                <Button size="sm" variant="outline" onClick={handleResendConfirmation} disabled={resending}>
                  {resending ? 'Resending…' : 'Resend confirmation email'}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Magic Link removed per product decision */}

        <p className="mt-10 text-center text-sm text-gray-600">
          Don't have an account?{" "}
          <Link href="/signup" className="font-semibold leading-6 text-primary-brand hover:text-primary-brand/80">
            Sign Up
          </Link>
        </p>
      </div>
    </div>
  )
}
