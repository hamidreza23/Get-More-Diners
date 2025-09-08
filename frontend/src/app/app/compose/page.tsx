'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, APIError, AIOfferRequest } from '../../../lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Icon } from '@/components/ui/icon'
import { toast } from 'sonner'

const cuisineTypes = ['Italian','Mexican','Japanese','American','French','Indian','Thai','Chinese','Seafood','Steakhouse']
const tones = ['friendly','formal','playful','professional','casual','urgent']
const goals = [
  'Promote new menu item',
  'Increase reservations',
  'Holiday special',
  'Happy hour promotion',
  'Weekend brunch',
  'Customer retention',
  'Drive traffic during slow hours',
  'Introduce seasonal dishes',
  'Celebrate anniversary or milestone',
  'Promote catering services',
  'Increase takeout orders',
  'Build loyalty program awareness'
]

const constraintSuggestions = [
  'Mention specific dishes (e.g., "Try our signature pasta")',
  'Include discount percentage (e.g., "20% off")',
  'Add time limit (e.g., "This week only")',
  'Include call-to-action (e.g., "Book now", "Order today")',
  'Mention location or directions',
  'Add opening hours',
  'Include phone number for reservations',
  'Mention special dietary options',
  'Reference local events or seasons',
  'Add urgency (e.g., "Limited time", "While supplies last")'
]

export default function ComposePage() {
  const router = useRouter()
  const [setup, setSetup] = useState({ cuisineType: '', tone: 'friendly', channel: 'email' as 'email'|'sms', goal: '', constraints: '' })
  const [campaignName, setCampaignName] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [sending, setSending] = useState(false)
  const [selectedCount, setSelectedCount] = useState(0)
  const [audienceEstimate, setAudienceEstimate] = useState<number | null>(null)
  const [lengthInfo, setLengthInfo] = useState<{subject?: number; body: number; limit: number}>({ body: 0, limit: 0 })

  useEffect(() => {
    const ids = JSON.parse(sessionStorage.getItem('selectedDiners') || '[]') as string[]
    setSelectedCount(ids.length)
    // Audience functionality temporarily disabled
    setAudienceEstimate(null)
  }, [])

  const handleBackToSearch = () => {
    // Store the current channel so search page can filter by appropriate consent
    sessionStorage.setItem('campaignChannel', setup.channel)
    router.push('/app/search')
  }



  const handleAIGenerate = async () => {
    if (!setup.cuisineType || !setup.goal) {
      toast.error('Please select cuisine type and goal')
      return
    }
    setIsGenerating(true)
    try {
      console.log('Generating AI content with payload:', {
        cuisine: setup.cuisineType,
        tone: setup.tone,
        channel: setup.channel,
        goal: setup.goal,
        constraints: setup.constraints || undefined,
      })
      
      const payload: AIOfferRequest = {
        cuisine: setup.cuisineType,
        tone: setup.tone,
        channel: setup.channel,
        goal: setup.goal,
        constraints: setup.constraints || undefined,
      }
      const res = await api.generateOffer(payload)
      console.log('AI generation response:', res)
      
      if (res.channel === 'email') {
        setSubject(res.content.subject || '')
      }
      setMessage(res.content.body)
      toast.success('AI content generated successfully!')
      
      // Update length info
      setLengthInfo({
        subject: res.content.subject?.length,
        body: res.content.body.length,
        limit: setup.channel === 'email' ? 500 : 160
      })
    } catch (error) {
      console.error('AI generation error:', error)
      if (error instanceof APIError) {
        if (error.status === 401) { 
          toast.error('Authentication required. Please sign in again.')
          router.push('/signin'); 
          return 
        }
        toast.error(error.message || 'Failed to generate content')
      } else {
        toast.error('An unexpected error occurred: ' + (error instanceof Error ? error.message : 'Unknown error'))
      }
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSend = async () => {
    if (!message || (setup.channel === 'email' && !subject)) {
      toast.error('Please generate or enter subject and message')
      return
    }
    if (!campaignName.trim()) {
      toast.error('Please enter a campaign name')
      return
    }
    setSending(true)
    try {
      const lastFilters = sessionStorage.getItem('lastSearchFilters')
      const filters = lastFilters ? JSON.parse(lastFilters) : { match: 'any' }
      const res = await api.createCampaign({
        channel: setup.channel,
        name: campaignName,
        subject: setup.channel === 'email' ? subject : undefined,
        body: message,
        filters,
      })
      toast.success('Campaign starts')
      router.push('/app/campaigns')
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 401) { router.push('/signin'); return }
        toast.error(error.message || 'Failed to send campaign')
      } else {
        toast.error('An unexpected error occurred')
      }
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <main className="flex-1 justify-center py-10">
        <div className="w-full max-w-4xl mx-auto px-4 space-y-12">
          {/* Header with Back Button */}
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Button 
                variant="outline" 
                onClick={handleBackToSearch}
                className="flex items-center gap-2"
              >
                <Icon name="arrow_back" />
                Back to Search
              </Button>
              <div className="flex-1">
                <h1 className="text-slate-900 text-4xl font-bold tracking-tight">Create a New Campaign</h1>
                <p className="text-slate-500 text-lg">Reach your customers with an AI-powered marketing campaign.</p>
              </div>
            </div>
            
          </div>

          <div className="space-y-8 rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
            <div className="space-y-2">
              <h2 className="text-slate-800 text-xl font-bold leading-tight tracking-[-0.015em]">1. Campaign Setup</h2>
              <p className="text-slate-500">Define the basic parameters for your campaign.</p>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="flex flex-col">
                <label className="text-slate-800 text-sm font-medium leading-normal pb-2">Campaign Name <span className="text-red-500">*</span></label>
                <Input 
                  className="h-11" 
                  value={campaignName} 
                  onChange={(e)=>setCampaignName(e.target.value)} 
                  placeholder="e.g., Summer Menu Launch, Holiday Special, etc." 
                  required
                />
                <p className="text-xs text-slate-500 mt-1">Give your campaign a memorable name for easy identification</p>
              </div>
              <div className="flex flex-col">
                <label className="text-slate-800 text-sm font-medium leading-normal pb-2">Cuisine Type</label>
                <Select value={setup.cuisineType} onValueChange={(v) => setSetup(prev=>({...prev, cuisineType: v}))}>
                  <SelectTrigger className="h-11"><SelectValue placeholder="Select cuisine type" /></SelectTrigger>
                  <SelectContent>
                    {cuisineTypes.map(t => (<SelectItem key={t} value={t}>{t}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col">
                <label className="text-slate-800 text-sm font-medium leading-normal pb-2">Tone</label>
                <Select value={setup.tone} onValueChange={(v) => setSetup(prev=>({...prev, tone: v}))}>
                  <SelectTrigger className="h-11"><SelectValue placeholder="Select tone" /></SelectTrigger>
                  <SelectContent>
                    {tones.map(t => (<SelectItem key={t} value={t}>{t[0].toUpperCase()+t.slice(1)}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col">
                <label className="text-slate-800 text-sm font-medium leading-normal pb-2">Channel</label>
                <Select value={setup.channel} onValueChange={(v: 'email'|'sms') => setSetup(prev=>({...prev, channel: v}))}>
                  <SelectTrigger className="h-11"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="sms">SMS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col">
                <label className="text-slate-800 text-sm font-medium leading-normal pb-2">Goal</label>
                <Select value={setup.goal} onValueChange={(v) => setSetup(prev=>({...prev, goal: v}))}>
                  <SelectTrigger className="h-11"><SelectValue placeholder="Select campaign goal" /></SelectTrigger>
                  <SelectContent>
                    {goals.map(g => (<SelectItem key={g} value={g}>{g}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2 flex flex-col">
                <label className="text-slate-800 text-sm font-medium leading-normal pb-2">Constraints & Instructions</label>
                <Textarea 
                  className="min-h-24" 
                  placeholder="e.g., mention lunch specials, include 20% discount, add phone number for reservations" 
                  value={setup.constraints} 
                  onChange={(e)=>setSetup(prev=>({...prev, constraints: e.target.value}))} 
                />
                <div className="mt-2">
                  <p className="text-xs text-slate-600 mb-2">💡 Quick suggestions (click to add):</p>
                  <div className="flex flex-wrap gap-2">
                    {constraintSuggestions.slice(0, 4).map((suggestion, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          const newConstraints = setup.constraints 
                            ? `${setup.constraints}, ${suggestion.split('(')[0].trim().toLowerCase()}`
                            : suggestion.split('(')[0].trim().toLowerCase()
                          setSetup(prev => ({...prev, constraints: newConstraints}))
                        }}
                        className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded border text-slate-700"
                      >
                        {suggestion.split('(')[0].trim()}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-8 rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
            <div className="space-y-2">
              <h2 className="text-slate-800 text-xl font-bold leading-tight tracking-[-0.015em]">2. AI Generation</h2>
              <p className="text-slate-500">Let our AI craft the perfect message for you.</p>
            </div>
            
            <Button onClick={handleAIGenerate} disabled={isGenerating} className="flex w-full items-center justify-center gap-2 rounded-md h-11 px-4 bg-[#13a4ec] text-white text-base font-bold hover:bg-[#1193d4]">
              <Icon name="auto_awesome" />
              <span className="truncate">{isGenerating ? 'Generating...' : 'Generate Content'}</span>
            </Button>
{message && (
              <div className="space-y-6">
                {setup.channel === 'email' && (
                  <div>
                    <label className="text-slate-800 text-sm font-medium leading-normal pb-2 block">Subject Line</label>
                    <Input className="h-11" value={subject} onChange={(e)=>setSubject(e.target.value)} placeholder="Enter your subject line" />
                  </div>
                )}
                <div>
                  <label className="text-slate-800 text-sm font-medium leading-normal pb-2 block">Message Body</label>
                  <Textarea className="min-h-36" value={message} onChange={(e)=>setMessage(e.target.value)} placeholder="Enter your message" />
                  <p className="text-xs text-slate-500 mt-2">
                    💡 Use <code className="bg-slate-100 px-1 rounded">{"{FirstName}"}</code> to personalize messages with the recipient's name
                  </p>
                </div>
                
                {/* Preview Section */}
                <div className="border rounded-lg p-4 bg-slate-50">
                  <h4 className="text-sm font-medium text-slate-700 mb-3">📱 Preview with Sample Data</h4>
                  <div className="space-y-3">
                    {setup.channel === 'email' && subject && (
                      <div>
                        <label className="text-xs text-slate-600 font-medium">Subject:</label>
                        <div className="bg-white border rounded p-2 text-sm">
                          {subject.replace(/\{FirstName\}/g, '<span class="bg-yellow-100 px-1 rounded">John</span>').replace(/<span class="bg-yellow-100 px-1 rounded">([^<]+)<\/span>/g, (match, name) => name)}
                        </div>
                      </div>
                    )}
                    <div>
                      <label className="text-xs text-slate-600 font-medium">Message:</label>
                      <div className="bg-white border rounded p-3 text-sm leading-relaxed">
                        <div
                          dangerouslySetInnerHTML={{
                            __html: message
                              .replace(/\{FirstName\}/g, '<span class="bg-yellow-100 px-1 rounded font-medium">John</span>')
                              .replace(/\n/g, '<br/>')
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {setup.channel === 'email' ? (
                    <>
                      <span className="text-xs rounded border px-2 py-1 bg-slate-100">Subject: {(subject || '').length} chars</span>
                      <span className={`text-xs rounded border px-2 py-1 ${message.length <= 500 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        Body: {message.length}/500 chars
                      </span>
                      {message.includes('{FirstName}') && (
                        <span className="text-xs rounded border px-2 py-1 bg-blue-100 text-blue-700">✓ Personalized</span>
                      )}
                    </>
                  ) : (
                    <>
                      <span className={`text-xs rounded border px-2 py-1 ${message.length <= 160 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        SMS: {message.length}/160 chars
                      </span>
                      {message.includes('{FirstName}') && (
                        <span className="text-xs rounded border px-2 py-1 bg-blue-100 text-blue-700">✓ Personalized</span>
                      )}
                    </>
                  )}
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="outline" className="bg-transparent" onClick={()=>{setSubject(''); setMessage('')}}>
                    <Icon name="edit" />
                    <span className="truncate">Clear</span>
                  </Button>
                  <Button onClick={handleAIGenerate} className="bg-[#13a4ec] text-white hover:bg-[#1193d4]">
                    <Icon name="refresh" />
                    <span className="truncate">Regenerate</span>
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-8 rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
            <div className="space-y-4">
              <h2 className="text-slate-800 text-xl font-bold leading-tight tracking-[-0.015em]">3. Audience</h2>
              
              {/* Selected Audience Info */}
              {selectedCount > 0 ? (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6">
                  <div className="flex items-center gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                        <Icon name="group" className="text-emerald-600 w-6 h-6" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-emerald-900 text-lg">Selected Audience</h3>
                      <p className="text-emerald-700 text-sm mt-1">
                        {selectedCount} diner{selectedCount !== 1 ? 's' : ''} selected from your search
                      </p>
                      <p className="text-emerald-600 text-xs mt-2">
                        These diners will receive your campaign message
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <Link href="/app/search">
                        <Button variant="outline" size="sm" className="bg-white border-emerald-300 text-emerald-700 hover:bg-emerald-50">
                          <Icon name="edit" className="mr-2 w-4 h-4" />
                          Edit Selection
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-50 border rounded-lg p-6">
                  <div className="text-center py-4">
                    <div className="text-slate-400 mb-4">
                      <Icon name="people" className="mx-auto w-12 h-12" />
                    </div>
                    <p className="text-slate-600 font-medium mb-2">No Audience Selected</p>
                    <p className="text-sm text-slate-500 mb-4">
                      Select diners from the search page to create your campaign audience
                    </p>
                    <Link href="/app/search">
                      <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
                        <Icon name="search" className="mr-2" />
                        Search for Diners
                      </Button>
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-8 rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
            <div className="space-y-2">
              <h2 className="text-slate-800 text-xl font-bold leading-tight tracking-[-0.015em]">4. Send Campaign</h2>
              <p className="text-slate-500">Review your campaign details before sending it off.</p>
            </div>
            <Button onClick={handleSend} disabled={sending || !message || (setup.channel==='email' && !subject)} className="flex w-full items-center justify-center gap-2 rounded-md h-12 px-6 bg-green-500 text-white text-lg font-bold hover:bg-green-600">
              <Icon name="send" />
              <span className="truncate">{sending ? 'Sending...' : 'Confirm and Send Campaign'}</span>
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}
