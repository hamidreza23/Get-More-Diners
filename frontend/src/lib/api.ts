import { createClient } from '@/lib/supabase'

// Types
export interface Restaurant {
  id: string
  owner_user_id: string
  name: string
  cuisine?: string
  city?: string
  state?: string
  contact_email?: string
  contact_phone?: string
  website_url?: string
  logo_url?: string
  caption?: string
  created_at: string
}

export interface RestaurantInput {
  name: string
  cuisine?: string
  city?: string
  state?: string
  contact_email?: string
  contact_phone?: string
  website_url?: string
  logo_url?: string
  caption?: string
}

export interface Diner {
  phone: string  // Primary key from backend
  first_name?: string
  last_name?: string
  email?: string
  city?: string
  state?: string
  seniority?: string
  address?: string
  dining_interests?: string  // Comma-separated string
  interests?: string[]       // Parsed array
  consent_email?: boolean
  consent_sms?: boolean
}

export interface SearchDinersParams {
  city?: string
  state?: string
  interests?: string
  seniority?: string
  match?: 'any' | 'all'
  channel?: 'email' | 'sms'
  page?: number
  pageSize?: number
}

export interface SearchDinersResponse {
  items: Diner[]
  total: number
}

export interface FilterOptionsResponse {
  interests: string[]
  seniority_levels: string[]
  states: string[]
  cities: string[]
}

export interface AIOfferRequest {
  cuisine: string
  tone: string
  channel: 'email' | 'sms'
  goal: string
  constraints?: string
}

export interface AIOfferResponse {
  channel: string
  content: {
    subject?: string
    body: string
  }
  html_content?: string
  json_structure?: any
  preview: any
  metadata: {
    ai_generated: boolean
    length_email_subject?: number
    length_email_body?: number
    length_sms?: number
  }
}

export interface CampaignFilters {
  city?: string
  state?: string
  interests?: string[]
  match?: 'any' | 'all'
}

export interface CreateCampaignRequest {
  channel: 'email' | 'sms'
  name: string
  subject?: string
  body: string
  filters: CampaignFilters
}

export interface Campaign {
  id: string
  restaurant_id: string
  channel: string
  name?: string
  subject?: string
  body: string
  status?: string
  audience_filter_json?: any
  created_at: string
  audience_size?: number
  sent_count?: number
  failed_count?: number
  click_rate?: number
}

export interface CampaignRecipient {
  id: string
  campaign_id: string
  diner_id: string
  delivery_status: string
  preview_payload_json?: any
  diner?: Diner
}

export interface CampaignDetails extends Campaign {
  recipients: CampaignRecipient[]
}

export interface CampaignPreview {
  diner_id: string
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  rendered_message: string
}

// AI Food Image (Demo)
export interface FoodImageRequest {
  dishName: string
  ingredients: string[] | string
  style?: 'natural' | 'vivid' | 'rustic' | 'gourmet'
  size?: '512x512' | '768x768' | '1024x1024'
  variations?: number
}

export interface FoodImageResponse {
  images: string[]
  prompt: string
  metadata: any
}

export interface CreateCampaignResponse {
  campaignId: string
  audienceSize: number
  previews: CampaignPreview[]
}

// API Error class
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

// Base API client
class APIClient {
  private baseURL: string
  private supabase = createClient()

  constructor() {
    // Use environment variable for production, fallback to localhost for development
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const { data: { session } } = await this.supabase.auth.getSession()
    
    if (!session?.access_token) {
      throw new APIError('Authentication required', 401)
    }

    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const headers = await this.getAuthHeaders()
      
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      })

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`
        let errorData: any = null

        try {
          errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          // If we can't parse JSON, use status text
          errorMessage = response.statusText || errorMessage
        }

        throw new APIError(errorMessage, response.status, errorData)
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        return {} as T
      }

      return await response.json()
    } catch (error) {
      if (error instanceof APIError) {
        throw error
      }
      
      // Network or other errors
      throw new APIError(
        error instanceof Error ? error.message : 'Network error occurred',
        0
      )
    }
  }

  // Public request (no auth header)
  private async requestPublic<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
      })

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`
        let errorData: any = null
        try {
          errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = response.statusText || errorMessage
        }
        throw new APIError(errorMessage, response.status, errorData)
      }

      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        return {} as T
      }
      return await response.json()
    } catch (error) {
      if (error instanceof APIError) throw error
      throw new APIError(error instanceof Error ? error.message : 'Network error occurred', 0)
    }
  }

  // Restaurant API
  async getRestaurant(): Promise<Restaurant | null> {
    try {
      return await this.request<Restaurant>('/api/v1/me/restaurant')
    } catch (error) {
      if (error instanceof APIError && error.status === 404) {
        return null
      }
      throw error
    }
  }

  async upsertRestaurant(data: RestaurantInput): Promise<Restaurant> {
    return this.request<Restaurant>('/api/v1/me/restaurant', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Diners API
  async searchDiners(params: SearchDinersParams = {}): Promise<SearchDinersResponse> {
    const searchParams = new URLSearchParams()
    
    if (params.city) searchParams.append('city', params.city)
    if (params.state) searchParams.append('state', params.state)
    if (params.interests) searchParams.append('interests', params.interests)
    if (params.seniority) searchParams.append('seniority', params.seniority)
    if (params.match) searchParams.append('match', params.match)
    if (params.channel) searchParams.append('channel', params.channel)
    if (params.page) searchParams.append('page', params.page.toString())
    if (params.pageSize) searchParams.append('pageSize', params.pageSize.toString())

    const queryString = searchParams.toString()
    const endpoint = `/api/v1/diners${queryString ? `?${queryString}` : ''}`
    
    return this.request<SearchDinersResponse>(endpoint)
  }

  async getFilterOptions(): Promise<FilterOptionsResponse> {
    return this.request<FilterOptionsResponse>('/api/v1/diners/filter-options')
  }

  // Auth API - check if an email is registered
  async checkEmail(email: string): Promise<{ registered: boolean; confirmed?: boolean }> {
    const params = new URLSearchParams({ email })
    return this.requestPublic<{ registered: boolean; confirmed?: boolean }>(`/api/v1/auth/check-email?${params.toString()}`)
  }


  // AI API
  async generateOffer(data: AIOfferRequest): Promise<AIOfferResponse> {
    return this.request<AIOfferResponse>('/api/v1/ai/offer', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Campaigns API
  async createCampaign(data: CreateCampaignRequest): Promise<CreateCampaignResponse> {
    return this.request<CreateCampaignResponse>('/api/v1/campaigns', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async listCampaigns(): Promise<Campaign[]> {
    return this.request<Campaign[]>('/api/v1/campaigns')
  }

  async updateCampaignStatus(campaignId: string, status: 'active' | 'paused' | 'stopped'): Promise<void> {
    return this.request<void>(`/api/v1/campaigns/${campaignId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  }

  async deleteCampaign(campaignId: string): Promise<void> {
    return this.request<void>(`/api/v1/campaigns/${campaignId}`, {
      method: 'DELETE',
    })
  }

  async getCampaign(id: string): Promise<CampaignDetails> {
    return this.request<CampaignDetails>(`/api/v1/campaigns/${id}`)
  }

  // AI Food Image (Demo)
  async generateFoodImage(data: FoodImageRequest): Promise<FoodImageResponse> {
    // Map to backend schema
    const payload = {
      dish_name: data.dishName,
      ingredients: data.ingredients,
      style: data.style || 'natural',
      size: data.size || '768x768',
      variations: data.variations || 1,
    }
    return this.request<FoodImageResponse>('/api/v1/ai/food-image', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return fetch(`${this.baseURL}/health`).then(res => res.json())
  }
}

// Export singleton instance
export const api = new APIClient()

// Export error class for handling
