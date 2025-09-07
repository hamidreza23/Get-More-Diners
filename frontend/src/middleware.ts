import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Get user and session data
  const { data: { user }, error } = await supabase.auth.getUser()
  const { data: { session }, error: sessionError } = await supabase.auth.getSession()
  
  // Only check for protected routes - allow auth pages to always be accessible
  if (request.nextUrl.pathname.startsWith('/app')) {
    // For protected routes, check if user is properly authenticated
    if (!user || error || !session || sessionError) {
      return NextResponse.redirect(new URL('/signin', request.url))
    }
  }
  
  // Allow all other routes (including /signin, /signup, /) to be accessible
  // This means users can always access auth pages regardless of session state

  return supabaseResponse
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * Feel free to modify this pattern to include more paths.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
