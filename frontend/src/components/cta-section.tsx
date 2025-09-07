import { Button } from "@/components/ui/button"
import Link from "next/link"

export function CTASection() {
  return (
    <section className="bg-orange-50 py-20 lg:py-28">
      <div className="mx-auto max-w-4xl px-4 text-center">
        <h2 className="text-4xl font-bold tracking-tighter text-gray-800 sm:text-5xl text-balance">
          Ready to Get More Diners?
        </h2>
        <p className="mt-4 text-lg text-gray-600">
          Join hundreds of restaurants already growing their customer base. Start your free trial today.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link href="/signup">
            <Button
              size="lg"
              className="bg-[var(--primary-color)] hover:bg-[var(--primary-color)]/90 text-white text-lg px-8 py-4 h-14"
            >
              Start Free Trial
            </Button>
          </Link>
          <Button
            size="lg"
            variant="secondary"
            className="bg-white text-gray-900 hover:bg-gray-200 text-lg px-8 py-4 h-14 shadow-sm"
          >
            Schedule Demo
          </Button>
        </div>
        <p className="mt-4 text-sm text-gray-500">No credit card required • 14-day free trial • Cancel anytime</p>
      </div>
    </section>
  )
}
