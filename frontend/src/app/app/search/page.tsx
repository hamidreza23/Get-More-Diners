"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Icon } from "@/components/ui/icon"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { api, type Diner, type SearchDinersParams, type FilterOptionsResponse } from "@/lib/api"
import { toast } from "sonner"

// Interest labels for display
const interestLabels: Record<string, string> = {
  "fine_dining": "Fine Dining",
  "pubs": "Pubs & Bars",
  "coffee_shops": "Coffee Shops", 
  "fast_food": "Fast Food",
  "ethnic_cuisine": "Ethnic Cuisine",
  "vegetarian": "Vegetarian",
  "steakhouse": "Steakhouse",
  "seafood": "Seafood",
  "italian": "Italian",
  "mexican": "Mexican"
}

export default function SearchPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [selectedDiners, setSelectedDiners] = useState<string[]>([])
  const [diners, setDiners] = useState<Diner[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(25)
  const [filterOptions, setFilterOptions] = useState<FilterOptionsResponse>({
    interests: [],
    seniority_levels: [],
    states: [],
    cities: []
  })
  
  const [searchFilters, setSearchFilters] = useState({
    city: "",
    state: "",
    interests: [] as string[],
    seniority: [] as string[],
    consentEmail: false,
    consentSms: false,
    match: "any" as "any" | "all"
  })
  const [campaignChannel, setCampaignChannel] = useState<'email' | 'sms' | null>(null)

  // Load filter options on component mount
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const options = await api.getFilterOptions()
        setFilterOptions(options)
      } catch (error) {
        console.error('Failed to load filter options:', error)
        toast.error('Failed to load filter options')
      }
    }
    loadFilterOptions()
  }, [])

  // Auto-search when filters change or on initial load
  useEffect(() => {
    handleSearch()
  }, [searchFilters, currentPage, campaignChannel])

  // Restore selected diners and campaign channel when coming back from compose page
  useEffect(() => {
    const savedSelections = JSON.parse(sessionStorage.getItem('selectedDiners') || '[]') as string[]
    if (savedSelections.length > 0) {
      setSelectedDiners(savedSelections)
    }
    
    // Get campaign channel from sessionStorage
    const channel = sessionStorage.getItem('campaignChannel') as 'email' | 'sms' | null
    setCampaignChannel(channel)
  }, [])

  const handleSearch = async () => {
    setSearching(true)
    try {
      const params: SearchDinersParams = {
        page: currentPage,
        pageSize: pageSize,
        match: searchFilters.match,
        channel: campaignChannel || undefined
      }

      if (searchFilters.city.trim()) {
        params.city = searchFilters.city.trim()
      }

      if (searchFilters.state && searchFilters.state !== "all") {
        params.state = searchFilters.state
      }

      if (searchFilters.interests.length > 0) {
        params.interests = searchFilters.interests.join(",")
      }

      if (searchFilters.seniority.length > 0) {
        params.seniority = searchFilters.seniority.join(",")
      }

      const result = await api.searchDiners(params)
      setDiners(result.items)
      setTotalCount(result.total)
      
      // Store search filters for campaign creation
      sessionStorage.setItem('lastSearchFilters', JSON.stringify(searchFilters))
      
      toast.success(`Found ${result.total} potential diners`)
    } catch (error) {
      console.error('Search error:', error)
      toast.error('Failed to search diners. Please try again.')
      setDiners([])
      setTotalCount(0)
    } finally {
      setSearching(false)
    }
  }

  const handleDinerSelect = (dinerPhone: string) => {
    setSelectedDiners(prev => 
      prev.includes(dinerPhone) 
        ? prev.filter(phone => phone !== dinerPhone)
        : [...prev, dinerPhone]
    )
  }

  const handleSelectAll = () => {
    if (selectedDiners.length === diners.length) {
      setSelectedDiners([])
    } else {
      setSelectedDiners(diners.map(diner => diner.phone))
    }
  }

  const handleSelectAllMatching = async () => {
    try {
      setLoading(true)
      // Get all diners matching current filters (without pagination)
      const params: SearchDinersParams = {
        page: 1,
        pageSize: 1000, // Large number to get all matching diners
        match: searchFilters.match,
        channel: campaignChannel || undefined
      }

      if (searchFilters.city.trim()) {
        params.city = searchFilters.city.trim()
      }

      if (searchFilters.state && searchFilters.state !== "all") {
        params.state = searchFilters.state
      }

      if (searchFilters.interests.length > 0) {
        params.interests = searchFilters.interests.join(",")
      }

      if (searchFilters.seniority.length > 0) {
        params.seniority = searchFilters.seniority.join(",")
      }

      const result = await api.searchDiners(params)
      const allMatchingDiners = result.items.map(diner => diner.phone)
      
      setSelectedDiners(allMatchingDiners)
      toast.success(`Selected all ${allMatchingDiners.length} matching diners`)
    } catch (error) {
      console.error('Error selecting all matching diners:', error)
      toast.error('Failed to select all matching diners')
    } finally {
      setLoading(false)
    }
  }

  const handleInterestToggle = (interest: string) => {
    setSearchFilters(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }))
  }

  const handleSeniorityToggle = (seniority: string) => {
    setSearchFilters(prev => ({
      ...prev,
      seniority: prev.seniority.includes(seniority)
        ? prev.seniority.filter(s => s !== seniority)
        : [...prev.seniority, seniority]
    }))
  }

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`
  }

  const handleCreateCampaign = () => {
    if (selectedDiners.length === 0) {
      toast.error('Please select at least one diner')
      return
    }
    
    // Store selected diners for campaign creation
    sessionStorage.setItem('selectedDiners', JSON.stringify(selectedDiners))
    
    // Navigate to compose page
    router.push('/app/compose')
  }


  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#1a1a1a]">Find Potential Diners</h1>
            <p className="mt-2 text-[#666666]">
              Search our database of {totalCount.toLocaleString()} potential customers and create targeted campaigns
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            {selectedDiners.length > 0 && (
              <Button 
                variant="outline"
                onClick={() => {
                  // Scroll to selected diners or show them in a modal
                  const selectedElements = document.querySelectorAll('[data-selected="true"]')
                  if (selectedElements.length > 0) {
                    selectedElements[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
                  }
                }}
                className="bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
              >
                <Icon name="visibility" className="mr-2" />
                View Selected ({selectedDiners.length})
              </Button>
            )}
            <Button 
              onClick={handleCreateCampaign}
              disabled={selectedDiners.length === 0}
              className="bg-[#ea2a33] hover:bg-[#d0262d] text-white shadow-lg"
              size="lg"
            >
              <Icon name="campaign" className="mr-2" />
              Create Campaign ({selectedDiners.length})
            </Button>
          </div>
        </div>


        <div className="grid gap-6 lg:grid-cols-4">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Icon name="tune" />
                  Search Filters
                </CardTitle>
                <CardDescription>Narrow down your search</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Location Filters */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-slate-700 flex items-center gap-2">
                    <Icon name="location_on" className="text-sm" />
                    Location
                  </h3>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">City</label>
                    <div className="relative">
                      <Icon
                        name="location_city"
                        className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                      />
                      <Input
                        placeholder="Enter city name"
                        value={searchFilters.city}
                        onChange={(e) => setSearchFilters(prev => ({ ...prev, city: e.target.value }))}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">State</label>
                    <Select
                      value={searchFilters.state}
                      onValueChange={(value) => setSearchFilters(prev => ({ ...prev, state: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select state" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All States</SelectItem>
                        {filterOptions.states.map((state) => (
                          <SelectItem key={state} value={state}>
                            {state}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Dining Interests */}
                <div>
                  <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <Icon name="restaurant" className="text-sm" />
                    Dining Interests
                  </h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {filterOptions.interests.map((interest) => (
                      <div key={interest} className="flex items-center space-x-2">
                        <Checkbox
                          id={interest}
                          checked={searchFilters.interests.includes(interest)}
                          onCheckedChange={() => handleInterestToggle(interest)}
                        />
                        <label htmlFor={interest} className="text-sm text-slate-700">
                          {interestLabels[interest] || interest}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Seniority Level */}
                <div>
                  <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <Icon name="work" className="text-sm" />
                    Seniority Level
                  </h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {filterOptions.seniority_levels.map((seniority) => (
                      <div key={seniority} className="flex items-center space-x-2">
                        <Checkbox
                          id={seniority}
                          checked={searchFilters.seniority.includes(seniority)}
                          onCheckedChange={() => handleSeniorityToggle(seniority)}
                        />
                        <label htmlFor={seniority} className="text-sm text-slate-700">
                          {seniority}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Communication Consent */}
                <div>
                  <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <Icon name="mail" className="text-sm" />
                    Communication Consent
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="consent-email"
                        checked={searchFilters.consentEmail}
                        onCheckedChange={(checked) => setSearchFilters(prev => ({ ...prev, consentEmail: !!checked }))}
                      />
                      <label htmlFor="consent-email" className="text-sm text-slate-700">
                        Email Consent
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="consent-sms"
                        checked={searchFilters.consentSms}
                        onCheckedChange={(checked) => setSearchFilters(prev => ({ ...prev, consentSms: !!checked }))}
                      />
                      <label htmlFor="consent-sms" className="text-sm text-slate-700">
                        SMS Consent
                      </label>
                    </div>
                  </div>
                </div>

                {/* Match Type */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Interest Match</label>
                  <Select
                    value={searchFilters.match}
                    onValueChange={(value: "any" | "all") => setSearchFilters(prev => ({ ...prev, match: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">Any interest matches</SelectItem>
                      <SelectItem value="all">All interests match</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Filter Summary */}
                {(searchFilters.city || searchFilters.state !== "" || searchFilters.interests.length > 0) && (
                  <div className="pt-4 border-t border-slate-200">
                    <h4 className="text-sm font-medium text-slate-700 mb-2">Active Filters:</h4>
                    <div className="flex flex-wrap gap-1">
                      {searchFilters.city && (
                        <Badge variant="secondary" className="text-xs">
                          📍 {searchFilters.city}
                        </Badge>
                      )}
                      {searchFilters.state && searchFilters.state !== "all" && (
                        <Badge variant="secondary" className="text-xs">
                          🗺️ {searchFilters.state}
                        </Badge>
                      )}
                      {searchFilters.interests.map(interest => (
                        <Badge key={interest} variant="secondary" className="text-xs">
                          🍽️ {interestLabels[interest] || interest}
                        </Badge>
                      ))}
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setSearchFilters({ city: "", state: "", interests: [], seniority: [], consentEmail: false, consentSms: false, match: "any" })}
                      className="mt-2 w-full"
                    >
                      <Icon name="clear" className="mr-2" />
                      Clear All Filters
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Icon name="people" />
                      Search Results
                      {searching && <Icon name="refresh" className="animate-spin text-[#ea2a33]" />}
                    </CardTitle>
                    <CardDescription>
                      {searching ? "Searching..." : `${totalCount.toLocaleString()} potential diners found`}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedDiners.length > 0 && (
                      <Badge variant="secondary" className="bg-[#ea2a33] text-white">
                        {selectedDiners.length} selected
                      </Badge>
                    )}
                    <div className="flex items-center gap-2">
                      <Button variant="outline" onClick={handleSelectAll} className="bg-transparent">
                        <Icon
                          name={selectedDiners.length === diners.length ? "check_box" : "check_box_outline_blank"}
                          className="mr-2"
                        />
                        {selectedDiners.length === diners.length ? "Deselect Page" : "Select Page"}
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={handleSelectAllMatching} 
                        className="bg-transparent"
                        disabled={loading}
                      >
                        <Icon name="select_all" className="mr-2" />
                        Select All Matching ({totalCount})
                      </Button>
                      {selectedDiners.length > 0 && (
                        <Button 
                          variant="outline" 
                          onClick={() => setSelectedDiners([])} 
                          className="bg-transparent text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Icon name="clear" className="mr-2" />
                          Clear All
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {searching ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <Icon name="hourglass_empty" className="mx-auto text-4xl text-slate-400 mb-4 animate-spin" />
                      <p className="text-slate-600">Searching diners...</p>
                    </div>
                  </div>
                ) : diners.length === 0 ? (
                  <div className="text-center py-12">
                    <Icon name="search_off" className="mx-auto text-6xl text-gray-300 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No diners found</h3>
                    <p className="text-gray-500">Try adjusting your search filters to find more results.</p>
                  </div>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2 xl:grid-cols-1">
                    {diners.map((diner) => (
                      <Card
                        key={diner.phone}
                        className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                          selectedDiners.includes(diner.phone)
                            ? "ring-2 ring-[#ea2a33] bg-red-50 shadow-md"
                            : "hover:border-gray-300"
                        }`}
                        onClick={() => handleDinerSelect(diner.phone)}
                      >
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <Avatar className="h-12 w-12 flex-shrink-0">
                              <AvatarFallback className="bg-[#ea2a33] text-white font-semibold">
                                {getInitials(diner.first_name || '', diner.last_name || '')}
                              </AvatarFallback>
                            </Avatar>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-3 mb-3">
                                <Checkbox
                                  checked={selectedDiners.includes(diner.phone)}
                                  onChange={() => handleDinerSelect(diner.phone)}
                                  className="flex-shrink-0"
                                />
                                <div className="flex-1">
                                  <h3 className="font-semibold text-lg text-[#1a1a1a] truncate">
                                    {diner.first_name} {diner.last_name}
                                  </h3>
                                  {diner.seniority && (
                                    <Badge variant="outline" className="mt-1">
                                      {diner.seniority}
                                    </Badge>
                                  )}
                                </div>
                              </div>

                              <div className="space-y-2 mb-4">
                                <div className="flex items-center gap-2 text-sm text-[#666666]">
                                  <Icon name="email" className="text-[#ea2a33] flex-shrink-0" />
                                  <span className="truncate">{diner.email}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-[#666666]">
                                  <Icon name="phone" className="text-[#ea2a33] flex-shrink-0" />
                                  <span>{diner.phone}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-[#666666]">
                                  <Icon name="location_on" className="text-[#ea2a33] flex-shrink-0" />
                                  <span>
                                    {diner.city}, {diner.state}
                                  </span>
                                </div>
                                {diner.address && (
                                  <div className="flex items-start gap-2 text-sm text-[#666666]">
                                    <Icon name="home" className="text-[#ea2a33] flex-shrink-0 mt-0.5" />
                                    <span className="line-clamp-2">{diner.address}</span>
                                  </div>
                                )}
                              </div>

                              <div>
                                <p className="text-xs font-medium text-gray-500 mb-2">DINING INTERESTS</p>
                                <div className="flex flex-wrap gap-2">
                                  {diner.interests && diner.interests.map((interest) => (
                                    <Badge
                                      key={interest}
                                      variant="secondary"
                                      className="text-xs bg-gray-100 text-gray-700 hover:bg-gray-200"
                                    >
                                      {interestLabels[interest] || interest}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Pagination Controls */}
            {totalCount > pageSize && (
              <div className="flex items-center justify-between mt-6">
                <div className="text-sm text-slate-600">
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} diners
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="flex items-center gap-1"
                  >
                    <Icon name="chevron_left" className="w-4 h-4" />
                    Previous
                  </Button>
                  
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.ceil(totalCount / pageSize) }, (_, i) => i + 1)
                      .filter(page => {
                        // Show first page, last page, current page, and pages around current
                        return page === 1 || 
                               page === Math.ceil(totalCount / pageSize) || 
                               Math.abs(page - currentPage) <= 1
                      })
                      .map((page, index, array) => {
                        const showEllipsis = index > 0 && page - array[index - 1] > 1
                        return (
                          <div key={page} className="flex items-center gap-1">
                            {showEllipsis && <span className="text-slate-400">...</span>}
                            <Button
                              variant={page === currentPage ? "default" : "outline"}
                              size="sm"
                              onClick={() => setCurrentPage(page)}
                              className="w-8 h-8 p-0"
                            >
                              {page}
                            </Button>
                          </div>
                        )
                      })}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(Math.ceil(totalCount / pageSize), prev + 1))}
                    disabled={currentPage >= Math.ceil(totalCount / pageSize)}
                    className="flex items-center gap-1"
                  >
                    Next
                    <Icon name="chevron_right" className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
 
