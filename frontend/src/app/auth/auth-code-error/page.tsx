import Link from 'next/link'
import { GetMoreDinersLogo } from '@/components/marketing/logos/get-more-diners-logo'

export default function AuthCodeErrorPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900 flex items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8 text-center">
        <div className="mx-auto mb-4 flex items-center justify-center">
          <GetMoreDinersLogo />
        </div>
        
        <div className="space-y-4">
          <h1 className="text-2xl font-bold text-gray-900">Authentication Error</h1>
          <p className="text-gray-600">
            Sorry, we couldn't sign you in. The authentication link may have expired or been used already.
          </p>
        </div>

        <div className="space-y-4">
          <Link 
            href="/signin"
            className="block w-full rounded-md bg-primary-brand px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-brand/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-brand"
          >
            Try Signing In Again
          </Link>
          
          <Link 
            href="/signup"
            className="block w-full rounded-md border border-gray-300 px-4 py-3 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-brand"
          >
            Create New Account
          </Link>
        </div>
      </div>
    </div>
  )
}
