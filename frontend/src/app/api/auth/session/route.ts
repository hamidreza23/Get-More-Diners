import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'

export async function GET(request: NextRequest) {
  try {
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll()
          },
          setAll() {
            /* no-op: we only need to read cookies here */
          },
        },
      }
    )

    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) {
      return NextResponse.json({ access_token: null }, { status: 401 })
    }
    return NextResponse.json({ access_token: session.access_token })
  } catch (e) {
    return NextResponse.json({ access_token: null }, { status: 500 })
  }
}

