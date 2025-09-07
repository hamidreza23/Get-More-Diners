"use client"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function HeroSection() {
  useAmbientAudioInit()
  return (
    <section className="relative py-20 lg:py-32">
      <div className="absolute inset-0">
        <img
          alt="Busy restaurant with diners and staff"
          className="h-full w-full object-cover blur-[2px]"
          src="https://images.unsplash.com/photo-1528605248644-14dd04022da1?q=80&w=2000&auto=format&fit=crop"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/55 to-black/65"></div>
        {/* Background ambient sound (looping). Some browsers require a user gesture to start audio. */}
        <audio id="ambient-sound" autoPlay loop playsInline preload="auto" className="hidden">
          <source src="/sound/restaurant.mp3" type="audio/mpeg" />
        </audio>
      </div>
      <div className="relative mx-auto max-w-4xl px-4 text-center">
        <h1 className="text-5xl font-black leading-tight tracking-tighter text-white sm:text-6xl lg:text-7xl text-balance">
          Find & Connect with Potential Diners Near You
        </h1>
        <p className="mt-6 text-lg text-gray-200 sm:text-xl text-pretty">
          Search our database of potential customers, send personalized offers via email and SMS, and grow your
          restaurant with targeted marketing campaigns.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link href="/signup">
            <Button
              size="lg"
              className="bg-[var(--primary-color)] hover:bg-[var(--primary-color)]/90 text-white text-lg px-8 py-4 h-14"
            >
              Start Finding Diners
            </Button>
          </Link>
          <Button
            size="lg"
            variant="secondary"
            className="bg-white text-gray-900 hover:bg-gray-200 text-lg px-8 py-4 h-14"
            onClick={() => {
              const audio = document.getElementById('ambient-sound') as HTMLAudioElement | null
              audio?.play().catch(() => {/* autoplay may be blocked until user gesture */})
            }}
            title="Enable ambient restaurant sound"
          >
            Watch Demo
          </Button>
        </div>
      </div>
    </section>
  )
}

// Ensure audio attempts to start on initial load; if blocked, start on first user gesture
export function useAmbientAudioInit() {
  useEffect(() => {
    const audio = document.getElementById('ambient-sound') as HTMLAudioElement | null
    if (!audio) return
    let pointerHandler: any
    let keyHandler: any
    try {
      audio.volume = 0.35
      audio.muted = true
      // attempt muted autoplay
      audio.play()
        .then(() => {
          const unmute = () => {
            audio.muted = false
            audio.play().catch(() => {})
          }
          pointerHandler = unmute
          keyHandler = unmute
          window.addEventListener('pointerdown', pointerHandler, { once: true })
          window.addEventListener('keydown', keyHandler, { once: true })
        })
        .catch(() => {
          const start = () => {
            audio.muted = false
            audio.play().catch(() => {})
          }
          pointerHandler = start
          keyHandler = start
          window.addEventListener('pointerdown', pointerHandler, { once: true })
          window.addEventListener('keydown', keyHandler, { once: true })
        })
    } catch {
      // ignore
    }

    // Cleanup when leaving landing page
    return () => {
      try {
        if (pointerHandler) window.removeEventListener('pointerdown', pointerHandler)
        if (keyHandler) window.removeEventListener('keydown', keyHandler)
        audio.pause()
        audio.currentTime = 0
      } catch {}
    }
  }, [])
}
