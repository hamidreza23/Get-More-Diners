import { Header } from "@/components/marketing/header"
import { HeroSection } from "@/components/marketing/hero-section"
import { FeaturesSection } from "@/components/marketing/features-section"
import { MenuGenerationSection } from "@/components/marketing/menu-generation-section"
import { TestimonialsSection } from "@/components/marketing/testimonials-section"
import { PricingSection } from "@/components/marketing/pricing-section"
import { CTASection } from "@/components/marketing/cta-section"
import { Footer } from "@/components/marketing/footer"

export default function HomePage() {
  return (
    <div className="relative flex size-full min-h-screen flex-col bg-white group/design-root overflow-x-hidden">
      <div className="layout-container flex h-full grow flex-col">
        <Header />
        <main className="flex-1">
          <HeroSection />
          <FeaturesSection />
          <MenuGenerationSection />
          <TestimonialsSection />
          <PricingSection />
          <CTASection />
        </main>
        <Footer />
      </div>
    </div>
  )
}
