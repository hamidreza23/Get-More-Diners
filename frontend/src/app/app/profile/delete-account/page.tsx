"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { AlertTriangle, Trash2 } from 'lucide-react'

export default function DeleteAccountPage() {
  const [isDeleting, setIsDeleting] = useState(false)
  const [confirmationText, setConfirmationText] = useState('')
  const [showConfirmation, setShowConfirmation] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  const handleDeleteAccount = async () => {
    if (confirmationText !== 'DELETE') {
      toast.error('Please type "DELETE" to confirm')
      return
    }

    setIsDeleting(true)
    try {
      // Get current user
      const { data: { user }, error: userError } = await supabase.auth.getUser()
      
      if (userError || !user) {
        throw new Error('Unable to get user information')
      }

      // Get session token
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      
      console.log('[Delete Account] Session debug:', {
        hasSession: !!session,
        hasAccessToken: !!session?.access_token,
        hasUser: !!session?.user,
        userId: session?.user?.id,
        sessionError: sessionError?.message
      })
      
      if (sessionError || !session?.access_token) {
        throw new Error('No valid session found. Please sign in again.')
      }

      // Call backend to delete all user data
      const apiUrl = 'http://localhost:8000'
      console.log('[Delete Account] Using API URL:', apiUrl)
      const response = await fetch(`${apiUrl}/api/v1/me/delete-account`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      })

      console.log('[Delete Account] API response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      })

      if (!response.ok) {
        const errorData = await response.text()
        console.error('[Delete Account] API error:', errorData)
        throw new Error(`Failed to delete account data: ${response.status} ${response.statusText}`)
      }

      // The backend will handle Supabase user deletion
      console.log('[Delete Account] Account deletion completed successfully')
      
      // Sign out from Supabase
      await supabase.auth.signOut()

      // Clear all local storage
      localStorage.clear()
      sessionStorage.clear()

      // Show success message
      toast.success('Account deleted successfully! You will not be able to sign in again with this account.')
      
      // Redirect to landing page
      router.push('/')
    } catch (error) {
      console.error('Error deleting account:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      toast.error(`Failed to delete account: ${errorMessage}`)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Card className="border-red-200">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <CardTitle className="text-2xl text-red-900">Delete Account</CardTitle>
            <CardDescription className="text-red-700">
              This action cannot be undone. This will permanently delete your account and remove all your data from our servers.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-semibold text-red-900 mb-2">What will be deleted:</h3>
              <ul className="text-sm text-red-800 space-y-1">
                <li>• Your restaurant profile and settings</li>
                <li>• All your marketing campaigns</li>
                <li>• Campaign recipient data</li>
                <li>• All application data associated with your account</li>
              </ul>
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                <p className="text-sm text-red-800">
                  <strong>Warning:</strong> After deletion, you will NOT be able to sign in again with this account. This action is permanent.
                </p>
              </div>
            </div>

            {!showConfirmation ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Are you sure you want to delete your account? This action is permanent and cannot be undone.
                </p>
                <Button 
                  onClick={() => setShowConfirmation(true)}
                  variant="destructive"
                  className="w-full"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Yes, Delete My Account
                </Button>
                <Button 
                  onClick={() => router.back()}
                  variant="outline"
                  className="w-full"
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="confirmation" className="text-sm font-medium">
                    To confirm, type <span className="font-bold text-red-600">DELETE</span> in the box below:
                  </Label>
                  <Input
                    id="confirmation"
                    type="text"
                    value={confirmationText}
                    onChange={(e) => setConfirmationText(e.target.value)}
                    placeholder="Type DELETE to confirm"
                    className="mt-2"
                  />
                </div>
                
                <div className="flex space-x-3">
                  <Button 
                    onClick={handleDeleteAccount}
                    disabled={isDeleting || confirmationText !== 'DELETE'}
                    variant="destructive"
                    className="flex-1"
                  >
                    {isDeleting ? 'Deleting...' : 'Delete Account'}
                  </Button>
                  <Button 
                    onClick={() => {
                      setShowConfirmation(false)
                      setConfirmationText('')
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
