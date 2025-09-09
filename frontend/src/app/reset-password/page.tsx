'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

export default function ResetPasswordPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    const ensureSession = async () => {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        toast.error('Your reset link is invalid or expired. Please request a new one.')
        router.replace('/signin')
      }
    }
    ensureSession()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters long')
      return
    }
    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.updateUser({ password })
      if (error) {
        setErrorMsg(error.message)
        toast.error(error.message)
      } else {
        toast.success('Password updated')
        router.replace('/app')
      }
    } catch (e) {
      setErrorMsg('Failed to update password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white text-gray-900">
      <div className="w-full max-w-md p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">Set a New Password</h1>
          <p className="mt-2 text-gray-600">Enter and confirm your new password below.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm New Password</Label>
            <Input
              id="confirm"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Retype your new password"
              required
            />
          </div>
          {errorMsg && <div className="text-sm text-red-600 border rounded p-3">{errorMsg}</div>}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Updating…' : 'Update Password'}
          </Button>
        </form>
      </div>
    </div>
  )
}
