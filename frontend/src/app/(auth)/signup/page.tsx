'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { GetMoreDinersLogo } from '@/components/marketing/logos/get-more-diners-logo'
import { toast } from 'sonner'

export default function SignUpPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [emailStatus, setEmailStatus] = useState<'idle'|'checking'|'available'|'registered'|'error'>('idle')
  const [emailHint, setEmailHint] = useState<string | null>(null)
  const [emailConfirmed, setEmailConfirmed] = useState<boolean | null>(null)
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
        // Ignore errors, let user stay on signup page
        console.log('[SignUp] Auth check error:', error)
      }
    }
    checkAuth()
  }, [])

  // Debounced email availability check for better UX
  useEffect(() => {
    setEmailHint(null)
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailStatus('idle')
      setEmailConfirmed(null)
      return
    }
    setEmailStatus('checking')
    const t = setTimeout(async () => {
      try {
        const res = await api.checkEmail(email)
        if (res.registered) {
          setEmailStatus('registered')
          setEmailConfirmed(!!res.confirmed)
          setEmailHint(
            res.confirmed === false
              ? 'This email started sign-up but is not confirmed yet. You can resend the confirmation email.'
              : 'This email is already registered. Please sign in or use Forgot password.'
          )
        } else {
          setEmailStatus('available')
          setEmailConfirmed(null)
          setEmailHint('Looks good — this email is available.')
        }
      } catch (e) {
        setEmailStatus('error')
        setEmailConfirmed(null)
        setEmailHint('Unable to check email right now.')
      }
    }, 500)
    return () => clearTimeout(t)
  }, [email])

  const handleResendConfirmation = async () => {
    setResending(true)
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.resend({
        type: 'signup',
        email,
        options: { emailRedirectTo: `${window.location.origin}/auth/callback?next=/app` }
      })
      if (error) {
        toast.error(error.message)
      } else {
        toast.success('Confirmation email resent. Please check your inbox.')
      }
    } catch (e) {
      toast.error('Failed to resend confirmation email')
    } finally {
      setResending(false)
    }
  }

  const handleEmailSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrorMsg(null)

    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      // Pre-check email registered/confirmed to provide accurate message
      try {
        const status = await api.checkEmail(email)
        if (status.registered) {
          if (status.confirmed) {
            setErrorMsg('An account with this email already exists. Please sign in or use Forgot password.')
            toast.error('Email already registered')
            return
          } else {
            setErrorMsg('This email is pending confirmation. Please check your inbox or resend the confirmation email.')
            return
          }
        }
      } catch {}
      const supabase = createClient()
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback?next=/app`,
        },
      })

      if (error) {
        toast.error(error.message)
      } else {
        toast.success('Check your email to confirm your account!')
      }
    } catch (error) {
      toast.error('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  // Magic Link removed per product decision – password-based signup only

  return (
    <div className="min-h-screen bg-white text-gray-900 flex items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center">
            <GetMoreDinersLogo />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Join Get More Diners</h1>
          <p className="mt-2 text-base text-gray-600">Create your restaurant account to get started.</p>
        </div>

        <form onSubmit={handleEmailSignUp} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="name@restaurant.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            className="text-gray-900 placeholder-gray-400 focus:border-primary-brand focus:ring-primary-brand"
          />
          {emailHint && (
            <p className={`text-xs mt-1 ${emailStatus === 'registered' ? 'text-red-600' : emailStatus === 'available' ? 'text-emerald-600' : 'text-slate-500'}`}>
              {emailHint}
            </p>
          )}
          {emailStatus === 'registered' && emailConfirmed === false && (
            <div className="mt-2">
              <Button size="sm" variant="outline" onClick={handleResendConfirmation} disabled={resending}>
                {resending ? 'Resending…' : 'Resend confirmation email'}
              </Button>
            </div>
          )}
        </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="At least 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="text-gray-900 placeholder-gray-400 focus:border-primary-brand focus:ring-primary-brand"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm-password">Confirm Password</Label>
            <Input
              id="confirm-password"
              name="confirm-password"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="text-gray-900 placeholder-gray-400 focus:border-primary-brand focus:ring-primary-brand"
            />
          </div>

          <Button
            type="submit"
            disabled={loading || (emailStatus === 'registered' && emailConfirmed !== false)}
            className="flex w-full justify-center rounded-md bg-primary-brand px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-brand/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-brand"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
        </form>

        {errorMsg && (
          <div className="rounded-md border p-3 text-sm text-red-600">{errorMsg}</div>
        )}

        <p className="mt-10 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link href="/signin" className="font-semibold leading-6 text-primary-brand hover:text-primary-brand/80">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
