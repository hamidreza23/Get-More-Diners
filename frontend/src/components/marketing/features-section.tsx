export function FeaturesSection() {
  const features = [
    {
      icon: "search",
      title: "Search Potential Diners",
      description:
        "Browse our database of potential customers in your area. Filter by location, interests, and dining preferences to find your ideal target audience.",
    },
    {
      icon: "campaign",
      title: "AI-Powered Offers",
      description:
        "Create compelling promotional messages with AI assistance. Generate personalized offers that resonate with your target diners and drive conversions.",
    },
    {
      icon: "send",
      title: "Email & SMS Campaigns",
      description:
        "Send your offers directly to potential customers via email or SMS. Track delivery, opens, and responses to measure campaign effectiveness.",
    },
  ]

  return (
    <section className="py-20 lg:py-28 bg-white" id="features">
      <div className="mx-auto max-w-6xl px-4">
        <div className="text-center">
          <h2 className="text-4xl font-bold tracking-tighter text-gray-800 sm:text-5xl text-balance">
            Everything You Need to Get More Diners
          </h2>
          <p className="mt-4 text-lg text-gray-600 text-pretty">
            Our platform provides restaurant owners with the tools to find, connect with, and convert potential
            customers into loyal diners.
          </p>
        </div>
        <div className="mt-16 grid gap-10 md:grid-cols-3">
          {features.map((feature, index) => (
            <div key={index} className="flex flex-col items-center text-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-orange-100 text-[var(--primary-color)]">
                <span className="material-symbols-outlined text-4xl">{feature.icon}</span>
              </div>
              <h3 className="mt-6 text-2xl font-bold text-gray-800">{feature.title}</h3>
              <p className="mt-2 text-gray-600 text-pretty">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

