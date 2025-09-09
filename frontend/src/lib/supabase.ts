import { createBrowserClient, createServerClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

// Client-side Supabase client
export const createClient = () =>
  createBrowserClient(supabaseUrl, supabaseAnonKey)

// Server-side Supabase client - only use in Server Components
export const createServerSupabaseClient = async () => {
  const { cookies } = await import('next/headers')
  const cookieStore = cookies()

  return createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll()
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options)
          })
        } catch (error) {
          // The `setAll` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
    },
  })
}

// Type definitions for our database
export type Database = {
  public: {
    Tables: {
      restaurants: {
        Row: {
          id: string
          owner_user_id: string
          name: string
          cuisine: string | null
          city: string | null
          state: string | null
          contact_email: string | null
          contact_phone: string | null
          created_at: string
        }
        Insert: {
          id?: string
          owner_user_id: string
          name: string
          cuisine?: string | null
          city?: string | null
          state?: string | null
          contact_email?: string | null
          contact_phone?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          owner_user_id?: string
          name?: string
          cuisine?: string | null
          city?: string | null
          state?: string | null
          contact_email?: string | null
          contact_phone?: string | null
          created_at?: string
        }
      }
      diners: {
        Row: {
          id: string
          first_name: string | null
          last_name: string | null
          seniority: string | null
          city: string | null
          state: string | null
          address_text: string | null
          interests: string[] | null
          email: string | null
          phone: string | null
          consent_email: boolean | null
          consent_sms: boolean | null
        }
        Insert: {
          id?: string
          first_name?: string | null
          last_name?: string | null
          seniority?: string | null
          city?: string | null
          state?: string | null
          address_text?: string | null
          interests?: string[] | null
          email?: string | null
          phone?: string | null
          consent_email?: boolean | null
          consent_sms?: boolean | null
        }
        Update: {
          id?: string
          first_name?: string | null
          last_name?: string | null
          seniority?: string | null
          city?: string | null
          state?: string | null
          address_text?: string | null
          interests?: string[] | null
          email?: string | null
          phone?: string | null
          consent_email?: boolean | null
          consent_sms?: boolean | null
        }
      }
      campaigns: {
        Row: {
          id: string
          restaurant_id: string
          channel: string
          subject: string | null
          body: string
          audience_filter_json: any | null
          created_at: string
        }
        Insert: {
          id?: string
          restaurant_id: string
          channel: string
          subject?: string | null
          body: string
          audience_filter_json?: any | null
          created_at?: string
        }
        Update: {
          id?: string
          restaurant_id?: string
          channel?: string
          subject?: string | null
          body?: string
          audience_filter_json?: any | null
          created_at?: string
        }
      }
      campaign_recipients: {
        Row: {
          id: string
          campaign_id: string
          diner_id: string
          delivery_status: string
          preview_payload_json: any | null
        }
        Insert: {
          id?: string
          campaign_id: string
          diner_id: string
          delivery_status: string
          preview_payload_json?: any | null
        }
        Update: {
          id?: string
          campaign_id?: string
          diner_id?: string
          delivery_status?: string
          preview_payload_json?: any | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}

// Create a typed client
export const typedSupabase = createClient()
