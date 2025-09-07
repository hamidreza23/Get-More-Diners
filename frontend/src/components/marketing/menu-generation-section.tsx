import Link from "next/link"

export function MenuGenerationSection() {
  return (
    <section className="py-16 lg:py-24 bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 grid gap-10 md:grid-cols-2 items-center">
        <div>
          <h2 className="text-4xl font-bold tracking-tight text-gray-900">
            AI Image Generation for Menus & Menu Design
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            Instantly turn your dishes and ingredients into eye-catching visuals and polished menu designs. Showcase
            specials, try new concepts, and refresh your look — without a photo shoot or a designer.
          </p>
          <ul className="mt-6 space-y-3 text-gray-700">
            <li className="flex items-start gap-2"><span className="material-symbols-outlined text-[var(--primary-color)]">magic_button</span> Photorealistic food images from ingredients</li>
            <li className="flex items-start gap-2"><span className="material-symbols-outlined text-[var(--primary-color)]">auto_awesome</span> Elegant, ready-to-print menu layouts</li>
            <li className="flex items-start gap-2"><span className="material-symbols-outlined text-[var(--primary-color)]">schedule</span> Perfect for seasonal or limited-time specials</li>
          </ul>
          <div className="mt-6">
            <Link href="/app/ai/food-studio" className="inline-flex items-center rounded-md bg-[var(--primary-color)] px-5 py-3 text-white hover:bg-[var(--primary-color)]/90">
              Try AI Food Studio
            </Link>
          </div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="aspect-square overflow-hidden rounded-lg bg-gray-100">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/sushi.png" alt="Menu image generation example" className="w-full h-full object-cover" />
            </div>
            <div className="aspect-square overflow-hidden rounded-lg bg-white border flex items-center justify-center">
              <div className="w-[90%] rounded-md border bg-gray-50 p-4 shadow-sm">
                <div className="text-center font-bold text-gray-800">Menu Design Preview</div>
                <div className="mt-3 space-y-2 text-sm">
                  <div className="flex items-center justify-between border-b pb-1">
                    <span>Margherita Pizza</span>
                    <span className="font-medium">$12</span>
                  </div>
                  <div className="flex items-center justify-between border-b pb-1">
                    <span>Truffle Risotto</span>
                    <span className="font-medium">$18</span>
                  </div>
                  <div className="flex items-center justify-between border-b pb-1">
                    <span>Sushi Platter</span>
                    <span className="font-medium">$22</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <p className="mt-3 text-sm text-gray-500 text-center">Examples: AI-generated dish visuals and a clean menu layout preview</p>
        </div>
      </div>
    </section>
  )
}
