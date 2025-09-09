'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import { api, APIError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

interface Campaign {
  id: string
  created_at: string
  channel: string
  subject?: string
  body: string
  audience_filter_json?: any
  recipients: CampaignRecipient[]
}

interface CampaignRecipient {
  id: string
  diner_id: string
  delivery_status: string
  preview_payload_json?: any
  diner?: {
    first_name?: string
    last_name?: string
    email?: string
    phone?: string
    city?: string
    state?: string
  }
}

export default function CampaignDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [loading, setLoading] = useState(true)

  const campaignId = params.id as string

  useEffect(() => {
    if (campaignId) {
      loadCampaign()
    }
  }, [campaignId])

  const loadCampaign = async () => {
    try {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) { router.push('/signin'); return }

      const data = await api.getCampaign(campaignId)
      setCampaign(data as any)
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 401) { router.push('/signin'); return }
        if (error.status === 404) { toast.error('Campaign not found'); router.push('/app/campaigns'); return }
        toast.error(error.message || 'Failed to load campaign')
      } else {
        console.error('Error loading campaign:', error)
        toast.error('An unexpected error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getChannelBadge = (channel: string) => {
    const variant = channel === 'email' ? 'default' : 'secondary'
    return (
      <Badge variant={variant} className="text-sm">
        {channel === 'email' ? '📧 Email' : '📱 SMS'}
      </Badge>
    )
  }

  const getStatusBadge = (status: string) => {
    const variant = status === 'simulated_sent' ? 'default' : 'destructive'
    const label = status === 'simulated_sent' ? 'Sent' : 'Failed'
    return <Badge variant={variant}>{label}</Badge>
  }

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
        <main className="container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-muted-foreground">Loading campaign details...</p>
          </div>
        </main>
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
        <main className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-2">Campaign Not Found</h1>
            <p className="text-muted-foreground mb-4">
              The campaign you're looking for doesn't exist or you don't have permission to view it.
            </p>
            <Button asChild>
              <Link href="/app/campaigns">Back to Campaigns</Link>
            </Button>
          </div>
        </main>
      </div>
    )
  }

  const successfulDeliveries = campaign.recipients.filter(r => r.delivery_status === 'simulated_sent').length
  const failedDeliveries = campaign.recipients.filter(r => r.delivery_status === 'simulated_failed').length

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
      <main className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <Button variant="outline" size="sm" asChild>
              <Link href="/app/campaigns">← Back to Campaigns</Link>
            </Button>
            {getChannelBadge(campaign.channel)}
          </div>
          <h1 className="text-3xl font-bold mb-2">
            {campaign.subject || `SMS Campaign`}
          </h1>
          <p className="text-muted-foreground">
            Created on {formatDate(campaign.created_at)}
          </p>
        </div>
      </div>

      {/* Campaign Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Recipients</CardTitle>
            <span className="text-2xl">👥</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaign.recipients.length}</div>
            <p className="text-xs text-muted-foreground">
              Messages sent
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
            <span className="text-2xl">✅</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{successfulDeliveries}</div>
            <p className="text-xs text-muted-foreground">
              {campaign.recipients.length > 0 ? Math.round((successfulDeliveries / campaign.recipients.length) * 100) : 0}% success rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <span className="text-2xl">❌</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{failedDeliveries}</div>
            <p className="text-xs text-muted-foreground">
              Delivery failures
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Channel</CardTitle>
            <span className="text-2xl">{campaign.channel === 'email' ? '📧' : '📱'}</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{campaign.channel}</div>
            <p className="text-xs text-muted-foreground">
              Communication channel
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Campaign Content */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Campaign Content</CardTitle>
          <CardDescription>
            The message content that was sent to recipients
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {campaign.subject && (
            <div>
              <h4 className="font-medium mb-2">Subject Line</h4>
              <div className="p-3 bg-muted rounded-md">
                <p className="font-medium">{campaign.subject}</p>
              </div>
            </div>
          )}
          
          <div>
            <h4 className="font-medium mb-2">
              {campaign.channel === 'email' ? 'Email Body' : 'SMS Message'}
            </h4>
            <div className="p-3 bg-muted rounded-md">
              <p className="whitespace-pre-wrap">{campaign.body}</p>
            </div>
          </div>

          {/* Content Stats */}
          <div className="flex flex-wrap gap-2">
            {campaign.channel === 'email' ? (
              <>
                <Badge variant="outline">
                  Subject: {campaign.subject?.length || 0} characters
                </Badge>
                <Badge variant="outline">
                  Body: {campaign.body.length} characters
                </Badge>
              </>
            ) : (
              <Badge variant="outline">
                Message: {campaign.body.length}/160 characters
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Campaign Filters */}
      {campaign.audience_filter_json && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Audience Filters</CardTitle>
            <CardDescription>
              The criteria used to select recipients for this campaign
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {campaign.audience_filter_json.city && (
                <div>
                  <Label className="text-sm font-medium">City</Label>
                  <p className="text-sm text-muted-foreground">{campaign.audience_filter_json.city}</p>
                </div>
              )}
              {campaign.audience_filter_json.state && (
                <div>
                  <Label className="text-sm font-medium">State</Label>
                  <p className="text-sm text-muted-foreground">{campaign.audience_filter_json.state}</p>
                </div>
              )}
              {campaign.audience_filter_json.interests && (
                <div>
                  <Label className="text-sm font-medium">Interests</Label>
                  <p className="text-sm text-muted-foreground">{campaign.audience_filter_json.interests}</p>
                </div>
              )}
              {campaign.audience_filter_json.match && (
                <div>
                  <Label className="text-sm font-medium">Match Type</Label>
                  <p className="text-sm text-muted-foreground">{campaign.audience_filter_json.match}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recipients Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recipients ({campaign.recipients.length})</CardTitle>
          <CardDescription>
            Detailed view of all campaign recipients and their delivery status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {campaign.recipients.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Recipient</TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Preview</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaign.recipients.slice(0, 25).map((recipient) => (
                    <TableRow key={recipient.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">
                            {recipient.diner?.first_name && recipient.diner?.last_name
                              ? `${recipient.diner.first_name} ${recipient.diner.last_name}`
                              : 'Unknown'
                            }
                          </div>
                          <div className="text-sm text-muted-foreground">
                            ID: {recipient.diner_id.substring(0, 8)}...
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {campaign.channel === 'email' ? recipient.diner?.email : recipient.diner?.phone}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {[recipient.diner?.city, recipient.diner?.state].filter(Boolean).join(', ') || 'N/A'}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(recipient.delivery_status)}
                      </TableCell>
                      <TableCell>
                        {recipient.preview_payload_json && (
                          <div className="max-w-xs">
                            <p className="text-sm truncate">
                              {recipient.preview_payload_json.subject || recipient.preview_payload_json.body}
                            </p>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {campaign.recipients.length > 25 && (
                <div className="p-4 text-center text-sm text-muted-foreground border-t">
                  Showing first 25 of {campaign.recipients.length} recipients
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📭</div>
              <h3 className="text-lg font-medium mb-2">No recipients</h3>
              <p className="text-muted-foreground">
                This campaign has no recipients
              </p>
            </div>
          )}
        </CardContent>
      </Card>
      </main>
    </div>
  )
}
