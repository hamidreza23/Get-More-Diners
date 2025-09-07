'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Icon } from '@/components/ui/icon'
// Demo-only: no backend call needed for image
import { toast } from 'sonner'

export default function FoodStudioPage() {
  const router = useRouter()
  const [dishName, setDishName] = useState('Margherita Pizza')
  const [ingredients, setIngredients] = useState('Tomato, Mozzarella, Basil, Olive oil, Pizza dough, Garlic')
  const [style, setStyle] = useState<'natural' | 'vivid' | 'rustic' | 'gourmet'>('natural')
  const [size, setSize] = useState<'512x512' | '768x768' | '1024x1024'>('768x768')
  const [variations, setVariations] = useState(1)
  const [loading, setLoading] = useState(false)
  const [images, setImages] = useState<string[]>([])
  const [prompt, setPrompt] = useState('')

  const handleGenerate = async () => {
    if (!dishName.trim()) { toast.error('Please enter a dish name'); return }
    setLoading(true)
    // Demo: show the local sushi image instantly
    try {
      setImages(['/sushi.png'])
      setPrompt(`Demo image for Sushi Platter — Tuna, Salmon, Avocado using local asset`)
      toast.success('Image generated (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = (src: string, idx: number) => {
    const a = document.createElement('a')
    a.href = src
    a.download = `${dishName.replace(/\s+/g, '_').toLowerCase()}_${idx + 1}.png`
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>AI Food Studio</CardTitle>
              <CardDescription>Enter a dish and ingredients; we’ll compose a photorealistic food image production menu. This is a demo feature.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-800 mb-2 block">Dish Name</label>
                    <Input value={dishName} onChange={(e)=>setDishName(e.target.value)} placeholder="e.g., Truffle Risotto" className="h-11" />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-800 mb-2 block">Ingredients (comma-separated)</label>
                    <Textarea value={ingredients} onChange={(e)=>setIngredients(e.target.value)} className="min-h-24" placeholder="e.g., Arborio rice, truffle, parmesan, butter, white wine" />
                    <p className="text-xs text-slate-500 mt-2">Tip: Use specific ingredients and garnishes for better detail.</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-slate-800 mb-2 block">Style</label>
                      <Select value={style} onValueChange={(v)=>setStyle(v as any)}>
                        <SelectTrigger className="h-11"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="natural">Natural</SelectItem>
                          <SelectItem value="vivid">Vivid</SelectItem>
                          <SelectItem value="rustic">Rustic</SelectItem>
                          <SelectItem value="gourmet">Gourmet</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-slate-800 mb-2 block">Size</label>
                      <Select value={size} onValueChange={(v)=>setSize(v as any)}>
                        <SelectTrigger className="h-11"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="512x512">512 x 512</SelectItem>
                          <SelectItem value="768x768">768 x 768</SelectItem>
                          <SelectItem value="1024x1024">1024 x 1024</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 items-end">
                    <div>
                      <label className="text-sm font-medium text-slate-800 mb-2 block">Variations</label>
                      <Input type="number" min={1} max={4} value={variations} onChange={(e)=>setVariations(Math.max(1, Math.min(4, Number(e.target.value)||1)))} className="h-11" />
                    </div>
                    <div className="flex justify-end">
                      <Button onClick={handleGenerate} disabled={loading} className="h-11 px-6 bg-[#13a4ec] hover:bg-[#1193d4] text-white font-semibold">
                        <Icon name="auto_awesome" className="mr-2" />
                        {loading ? 'Generating...' : 'Generate'}
                      </Button>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border bg-white p-4">
                  <p className="text-sm font-medium text-slate-700 mb-2">Sample Ideas</p>
                  <ul className="text-sm text-slate-600 space-y-2 list-disc pl-5">
                    <li onClick={()=>{setDishName('Sushi Platter'); setIngredients('Tuna, Salmon, Rice, Nori, Avocado, Cucumber, Soy sauce, Ginger')}} className="cursor-pointer hover:text-slate-800">Sushi Platter — Tuna, Salmon, Avocado</li>
                    <li onClick={()=>{setDishName('Vegan Buddha Bowl'); setIngredients('Quinoa, Chickpeas, Sweet potato, Kale, Avocado, Tahini')}} className="cursor-pointer hover:text-slate-800">Vegan Buddha Bowl — Quinoa & Chickpeas</li>
                    <li onClick={()=>{setDishName('Raspberry Cheesecake'); setIngredients('Cream cheese, Raspberry, Biscuits, Butter, Sugar')}} className="cursor-pointer hover:text-slate-800">Raspberry Cheesecake — Dessert</li>
                  </ul>
                  <p className="text-xs text-slate-500 mt-4">This is a demo preview. Images are AI-generated and not actual menu photography.</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>Result</CardTitle>
              <CardDescription>Preview and download your generated images.</CardDescription>
            </CardHeader>
            <CardContent>
              {!images.length ? (
                <div className="text-center text-slate-500 py-12">No image yet — enter details and click Generate.</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {images.map((src, idx) => (
                    <div key={idx} className="group rounded-lg overflow-hidden border bg-white">
                      <div className="relative aspect-square bg-slate-50">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={src} alt={`Generated ${idx+1}`} className="object-cover w-full h-full" />
                        <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition">
                          <Button size="sm" variant="secondary" onClick={()=>handleDownload(src, idx)} className="bg-white/90"> <Icon name="download" className="mr-1" /> Download</Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {prompt && (
                <div className="mt-6">
                  <p className="text-xs font-medium text-slate-700 mb-1">Prompt Used</p>
                  <div className="text-xs text-slate-600 bg-slate-50 rounded p-3 leading-relaxed">{prompt}</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
