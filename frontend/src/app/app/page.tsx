"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Icon } from "@/components/ui/icon"
import { api, type Campaign } from "../../lib/api"
import Link from "next/link"

export default function DashboardPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        const data = await api.listCampaigns()
        setCampaigns(data)
      } catch (error) {
        console.error('Failed to fetch campaigns:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchCampaigns()
  }, [])

  // Calculate real stats from campaigns
  const totalCampaigns = campaigns.length
  const totalSent = campaigns.reduce((sum, c) => sum + (c.sent_count || 0), 0)
  const totalRecipients = campaigns.reduce((sum, c) => sum + (c.audience_size || 0), 0)
  const avgClickRate = campaigns.length > 0 
    ? campaigns.reduce((sum, c) => sum + (c.click_rate || 0), 0) / campaigns.length 
    : 0

  const stats = [
    { title: "Total Campaigns", value: totalCampaigns.toString(), change: "All time", icon: "campaign" },
    { title: "Messages Sent", value: totalSent.toLocaleString(), change: "Total delivered", icon: "send" },
    { title: "Total Recipients", value: totalRecipients.toLocaleString(), change: "Audience reached", icon: "people" },
    { title: "Avg Click Rate", value: `${avgClickRate.toFixed(1)}%`, change: "Engagement rate", icon: "analytics" },
  ]

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#1a1a1a]">Dashboard</h1>
          <p className="mt-2 text-[#666666]">Welcome back! Here's what's happening with your restaurant.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          {stats.map((stat, index) => (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon name={stat.icon} className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.change}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Campaigns</CardTitle>
              <CardDescription>Your latest marketing campaigns</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center text-muted-foreground">Loading campaigns...</div>
              ) : campaigns.length === 0 ? (
                <div className="text-center text-muted-foreground">No campaigns yet</div>
              ) : (
                <div className="space-y-4">
                  {campaigns.slice(0, 3).map((campaign) => (
                    <div key={campaign.id} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{campaign.subject || `${campaign.channel.toUpperCase()} Campaign`}</p>
                        <p className="text-sm text-muted-foreground">
                          {campaign.sent_count || 0} sent • {campaign.click_rate || 0}% CTR
                        </p>
                      </div>
                      <Link href={`/app/campaigns/${campaign.id}`}>
                        <Button variant="outline" size="sm">
                          View
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance Overview</CardTitle>
              <CardDescription>Campaign metrics at a glance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Sent</span>
                  <span className="text-lg font-bold text-green-600">{totalSent.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Avg Click Rate</span>
                  <span className="text-lg font-bold text-blue-600">{avgClickRate.toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Recipients</span>
                  <span className="text-lg font-bold text-gray-600">{totalRecipients.toLocaleString()}</span>
                </div>
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Delivery Rate</span>
                    <span className="text-sm text-muted-foreground">
                      {totalRecipients > 0 ? ((totalSent / totalRecipients) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${totalRecipients > 0 ? (totalSent / totalRecipients) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Get started with common tasks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <Link href="/app/search">
                  <Button className="w-full bg-[#ea2a33] hover:bg-[#d0262d] text-white">
                    <Icon name="add" className="mr-2" />
                    Create New Campaign
                  </Button>
                </Link>
                <Link href="/app/search">
                  <Button variant="outline" className="w-full">
                    <Icon name="search" className="mr-2" />
                    Find Diners
                  </Button>
                </Link>
                <Link href="/app/profile">
                  <Button variant="outline" className="w-full">
                    <Icon name="settings" className="mr-2" />
                    Update Profile
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
