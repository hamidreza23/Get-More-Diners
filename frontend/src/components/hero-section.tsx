import { Button } from "@/components/ui/button"

export function HeroSection() {
  return (
    <section className="relative py-20 lg:py-32">
      <div className="absolute inset-0">
        <img
          alt="Restaurant ambiance"
          className="h-full w-full object-cover"
          src="/elegant-restaurant-interior-with-warm-lighting-and.jpg"
        />
        <div className="absolute inset-0 bg-black bg-opacity-50"></div>
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
          <Button
            size="lg"
            className="bg-[var(--primary-color)] hover:bg-[var(--primary-color)]/90 text-white text-lg px-8 py-4 h-14"
          >
            Start Finding Diners
          </Button>
          <Button
            size="lg"
            variant="secondary"
            className="bg-white text-gray-900 hover:bg-gray-200 text-lg px-8 py-4 h-14"
          >
            Watch Demo
          </Button>
        </div>
      </div>
    </section>
  )
}
