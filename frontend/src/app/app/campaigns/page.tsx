
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api, APIError, Campaign } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Icon } from '@/components/ui/icon'
import Link from 'next/link'
import { toast } from 'sonner'

export default function CampaignsPage() {
  const router = useRouter()
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.listCampaigns()
        setCampaigns(data)
      } catch (error) {
        if (error instanceof APIError) {
          if (error.status === 401) { router.push('/signin'); return }
          toast.error(error.message || 'Failed to load campaigns')
        } else {
          toast.error('An unexpected error occurred')
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [router])

  const getStatus = (c: Campaign) => 'Sent'

  const getStatusVariant = (status: string) => {
    return status === 'Sent' ? 'default' : status === 'Scheduled' ? 'secondary' : 'outline'
  }

  const handleStatusUpdate = async (campaignId: string, newStatus: 'active' | 'paused' | 'stopped') => {
    try {
      setUpdatingStatus(campaignId)
      await api.updateCampaignStatus(campaignId, newStatus)
      
      // Update local state
      setCampaigns(prev => prev.map(c => 
        c.id === campaignId ? { ...c, status: newStatus } : c
      ))
      
      const statusText = newStatus === 'active' ? 'resumed' : newStatus === 'paused' ? 'paused' : 'stopped'
      toast.success(`Campaign ${statusText} successfully`)
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 401) { router.push('/signin'); return }
        toast.error(error.message || 'Failed to update campaign status')
      } else {
        toast.error('An unexpected error occurred')
      }
    } finally {
      setUpdatingStatus(null)
    }
  }

  const handleRemoveCampaign = async (campaignId: string) => {
    if (!confirm('Are you sure you want to remove this campaign? This action cannot be undone.')) {
      return
    }
    
    try {
      setUpdatingStatus(campaignId)
      await api.deleteCampaign(campaignId)
      
      // Remove from local state
      setCampaigns(prev => prev.filter(c => c.id !== campaignId))
      
      toast.success('Campaign removed successfully')
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 401) { router.push('/signin'); return }
        toast.error(error.message || 'Failed to remove campaign')
      } else {
        toast.error('An unexpected error occurred')
      }
    } finally {
      setUpdatingStatus(null)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Campaign History</h1>
            <p className="mt-2 text-gray-600">View and manage your sent offers and marketing campaigns.</p>
          </div>
          <div className="flex gap-3">
            <Link href="/app/search"><Button variant="outline" className="bg-white border-gray-300 text-gray-700 hover:bg-gray-50"><Icon name="search" className="mr-2" />Find Diners</Button></Link>
            <Link href="/app/compose"><Button className="bg-[#ea2a33] hover:bg-[#d0262d] text-white px-6 py-3 rounded-lg font-medium"><Icon name="add" className="mr-2" />Create Offer</Button></Link>
          </div>
        </div>

        {loading ? (
          <div className="text-center text-muted-foreground">Loading campaigns...</div>
        ) : campaigns.length === 0 ? (
          <Card className="border-0 shadow-lg">
            <CardContent className="text-center py-16">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Icon name="campaign" className="text-3xl text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">No campaigns yet</h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">Create your first marketing campaign to start reaching potential customers and grow your restaurant business.</p>
              <Link href="/app/compose"><Button className="bg-[#ea2a33] hover:bg-[#d0262d] text-white shadow-lg px-8 py-3 rounded-lg font-medium">Create Your First Campaign</Button></Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {campaigns.map((c) => {
              const status = getStatus(c)
              const sent = c.sent_count || 0
              const waiting = Math.max((c.audience_size || 0) - (c.sent_count || 0) - (c.failed_count || 0), 0)
              const ctr = c.click_rate || 0
              const createdAt = c.created_at ? new Date(c.created_at).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
              }) : ''
              const isEmail = c.channel === 'email'
              return (
                <Card
                  key={c.id}
                  className="hover:shadow-lg transition-all duration-200"
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap mb-2">
                          <CardTitle className="truncate text-lg font-semibold text-gray-900">
                            {c.name || (isEmail ? (c.subject || 'Email Campaign') : 'SMS Campaign')}
                          </CardTitle>
                          <Badge variant={getStatusVariant(status)} className="text-xs">{status}</Badge>
                          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                            {c.channel.toUpperCase()}
                          </Badge>
                          {createdAt && (
                            <span className="text-xs text-gray-500">• {createdAt}</span>
                          )}
                        </div>

                        {/* Subject and Body */}
                        {isEmail && c.subject && (
                          <div className="text-sm text-gray-900 font-medium mb-1 truncate" title={c.subject}>
                            Subject: {c.subject}
                          </div>
                        )}
                        <div className="text-base text-gray-700 bg-gray-50 rounded-lg p-4 whitespace-pre-line line-clamp-6 leading-relaxed">
                          {c.body || ''}
                        </div>
                      </div>

                      <div className="flex flex-col gap-2 shrink-0">
                        {c.status === 'active' ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleStatusUpdate(c.id, 'paused')}
                            disabled={updatingStatus === c.id}
                            className="text-orange-600 border-orange-200 hover:bg-orange-50"
                          >
                            <Icon name="pause" className="mr-1" />
                            {updatingStatus === c.id ? 'Pausing...' : 'Pause'}
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleStatusUpdate(c.id, 'active')}
                            disabled={updatingStatus === c.id}
                            className="text-green-600 border-green-200 hover:bg-green-50"
                          >
                            <Icon name="play_arrow" className="mr-1" />
                            {updatingStatus === c.id ? 'Resuming...' : 'Resume'}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRemoveCampaign(c.id)}
                          disabled={updatingStatus === c.id}
                          className="text-red-600 border-red-200 hover:bg-red-50"
                        >
                          <Icon name="delete" className="mr-1" />
                          {updatingStatus === c.id ? 'Removing...' : 'Remove'}
                        </Button>
                      </div>
                    </div>

                    {/* Stats - compact */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                      <div className="rounded bg-green-50 border border-green-100 p-3 text-center">
                        <div className="text-[11px] uppercase tracking-wide text-green-700">Total Sent</div>
                        <div className="text-lg font-semibold text-green-700">{sent.toLocaleString()}</div>
                      </div>
                      <div className="rounded bg-amber-50 border border-amber-100 p-3 text-center">
                        <div className="text-[11px] uppercase tracking-wide text-amber-700">Waiting</div>
                        <div className="text-lg font-semibold text-amber-700">{waiting.toLocaleString()}</div>
                      </div>
                      <div className="rounded bg-blue-50 border border-blue-100 p-3 text-center">
                        <div className="text-[11px] uppercase tracking-wide text-blue-700">Total CTR</div>
                        <div className="text-lg font-semibold text-blue-700">{ctr}%</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
