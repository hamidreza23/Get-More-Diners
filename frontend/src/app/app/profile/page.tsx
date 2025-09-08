"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, APIError } from '../../../lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FormInput } from '@/components/ui/form-input'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { AlertTriangle } from 'lucide-react'

const CUISINE_TYPES = [
  'American', 'Italian', 'Mexican', 'Chinese', 'Japanese', 'Thai', 'Indian',
  'French', 'Mediterranean', 'Greek', 'Korean', 'Vietnamese', 'Brazilian',
  'Steakhouse', 'Seafood', 'Pizza', 'Burger', 'BBQ', 'Vegetarian', 'Vegan'
]

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

interface RestaurantFormData {
  name: string
  cuisine: string
  city: string
  state: string
  contact_email: string
  contact_phone: string
  website_url: string
  logo_url: string
  caption: string
}

export default function ProfilePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [restaurant, setRestaurant] = useState<RestaurantFormData>({
    name: '',
    cuisine: '',
    city: '',
    state: '',
    contact_email: '',
    contact_phone: '',
    website_url: '',
    logo_url: '',
    caption: ''
  })

  useEffect(() => {
    const loadRestaurant = async () => {
      try {
        const restaurantData = await api.getRestaurant()
        if (restaurantData) {
          setRestaurant({
            name: restaurantData.name || '',
            cuisine: restaurantData.cuisine || '',
            city: restaurantData.city || '',
            state: restaurantData.state || '',
            contact_email: restaurantData.contact_email || '',
            contact_phone: restaurantData.contact_phone || '',
            website_url: restaurantData.website_url || '',
            logo_url: restaurantData.logo_url || '',
            caption: restaurantData.caption || ''
          })
        }
      } catch (error) {
        if (error instanceof APIError) {
          if (error.status === 401) { router.push('/signin'); return }
          toast.error('Failed to load restaurant data')
        } else {
          toast.error('An unexpected error occurred')
        }
      } finally {
        setInitialLoading(false)
      }
    }
    loadRestaurant()
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.upsertRestaurant(restaurant)
      toast.success('Restaurant profile saved successfully!')
      router.push('/app/search')
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 401) { router.push('/signin'); return }
        toast.error(error.message || 'Failed to save restaurant profile')
      } else {
        toast.error('An unexpected error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof RestaurantFormData, value: string) => {
    setRestaurant(prev => ({ ...prev, [field]: value }))
  }

  if (initialLoading) {
    return (
      <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
        <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center text-muted-foreground">Loading profile...</div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="p-8">
            <div className="mb-8 text-center">
              <h2 className="text-4xl font-bold text-[#1a1a1a]">Restaurant Profile</h2>
              <p className="mt-2 text-md text-[#666666]">Update your restaurant's information to connect with more customers.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 gap-6">
                <FormInput id="restaurant-name" label="Restaurant Name" placeholder="e.g., The Gourmet Kitchen" required variant="dineconnect" value={restaurant.name} onChange={(e:any)=>handleInputChange('name', e.target.value)} />

                <div>
                  <label className="block text-sm font-medium text-[#1a1a1a]">Cuisine Type</label>
                  <Select value={restaurant.cuisine} onValueChange={(v)=>handleInputChange('cuisine', v)}>
                    <SelectTrigger className="mt-1 w-full h-11">
                      <SelectValue placeholder="Select cuisine type" />
                    </SelectTrigger>
                    <SelectContent>
                      {CUISINE_TYPES.map(c => (<SelectItem key={c} value={c}>{c}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1a1a1a]">Location</label>
                  <div className="mt-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput placeholder="City" label="" variant="dineconnect" value={restaurant.city} onChange={(e:any)=>handleInputChange('city', e.target.value)} />
                    <Select value={restaurant.state} onValueChange={(v)=>handleInputChange('state', v)}>
                      <SelectTrigger className="mt-1 w-full h-11"><SelectValue placeholder="State" /></SelectTrigger>
                      <SelectContent>
                        {US_STATES.map(s => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <FormInput id="contact-email" type="email" label="Contact Email" placeholder="e.g., contact@gourmet.com" variant="dineconnect" value={restaurant.contact_email} onChange={(e:any)=>handleInputChange('contact_email', e.target.value)} />
                <FormInput id="contact-phone" type="tel" label="Contact Phone" placeholder="e.g., (555) 123-4567" variant="dineconnect" value={restaurant.contact_phone} onChange={(e:any)=>handleInputChange('contact_phone', e.target.value)} />
                <FormInput id="website-url" type="url" label="Website/Resy URL" placeholder="e.g., https://resy.com/restaurant-name or https://restaurant.com" variant="dineconnect" value={restaurant.website_url} onChange={(e:any)=>handleInputChange('website_url', e.target.value)} />

                <div>
                  <label className="block text-sm font-medium text-[#1a1a1a] mb-2">Restaurant Logo <span className="text-gray-500">(Optional)</span></label>
                  <div className="flex items-center gap-4">
                    {restaurant.logo_url && (
                      <div className="w-16 h-16 rounded-lg overflow-hidden border-2 border-gray-200">
                        <img 
                          src={restaurant.logo_url} 
                          alt="Restaurant logo" 
                          className="w-full h-full object-cover"
                        />
                      </div>
                    )}
                    <div className="flex-1">
                      <FormInput 
                        id="logo-url" 
                        type="url" 
                        label="" 
                        placeholder="e.g., https://example.com/logo.png" 
                        variant="dineconnect" 
                        value={restaurant.logo_url} 
                        onChange={(e:any)=>handleInputChange('logo_url', e.target.value)} 
                      />
                      <p className="text-xs text-gray-500 mt-1">Enter a URL to your restaurant's logo image</p>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1a1a1a] mb-2">Restaurant Description <span className="text-gray-500">(Optional)</span></label>
                  <Textarea
                    id="caption"
                    rows={4}
                    placeholder="Describe your restaurant's atmosphere, specialties, and history..."
                    value={restaurant.caption}
                    onChange={(e) => handleInputChange('caption', e.target.value)}
                    className="resize-none"
                    maxLength={500}
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {restaurant.caption.length}/500 characters
                  </div>
                </div>
              </div>

              <div className="pt-6 flex justify-between items-center">
                <Link href="/app/profile/delete-account">
                  <Button 
                    type="button" 
                    variant="outline" 
                    className="text-red-600 border-red-300 hover:bg-red-50"
                  >
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </Link>
                
                <Button type="submit" className="inline-flex justify-center rounded-full border border-transparent bg-[#ea2a33] py-3 px-8 text-sm font-bold text-white hover:bg-[#d0262d]" disabled={loading || !restaurant.name}>
                  {loading ? 'Saving...' : 'Save Profile'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}
