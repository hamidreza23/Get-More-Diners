import { Button } from "@/components/ui/button"

export function PricingSection() {
  const plans = [
    {
      name: "Starter",
      description: "Perfect for small restaurants just getting started.",
      price: "$29",
      period: "/month",
      features: [
        "Search up to 500 diners/month",
        "Send 1,000 emails/month",
        "Basic AI offer generation",
        "Email support",
      ],
      popular: false,
    },
    {
      name: "Growth",
      description: "For restaurants ready to scale their customer outreach.",
      price: "$79",
      period: "/month",
      features: [
        "Search up to 2,000 diners/month",
        "Send 5,000 emails + 1,000 SMS/month",
        "Advanced AI offer generation",
        "Campaign analytics & tracking",
        "Priority support",
      ],
      popular: true,
    },
    {
      name: "Enterprise",
      description: "For restaurant chains and high-volume operations.",
      price: "Custom",
      period: "",
      features: [
        "Unlimited diner search",
        "Unlimited email & SMS sending",
        "Custom AI training",
        "Dedicated account manager",
        "White-label options",
      ],
      popular: false,
    },
  ]

  return (
    <section className="py-20 lg:py-28 bg-white" id="pricing">
      <div className="mx-auto max-w-6xl px-4">
        <div className="text-center">
          <h2 className="text-4xl font-bold tracking-tighter text-gray-800 sm:text-5xl">Simple, Transparent Pricing</h2>
          <p className="mt-4 text-lg text-gray-600">Choose the plan that fits your restaurant's growth goals.</p>
        </div>
        <div className="mt-16 grid gap-8 lg:grid-cols-3 lg:items-start">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`flex flex-col rounded-2xl p-8 shadow-sm relative ${
                plan.popular
                  ? "border-2 border-[var(--primary-color)] bg-white shadow-2xl"
                  : "border border-gray-200 bg-white"
              }`}
            >
              {plan.popular && (
                <p className="absolute top-0 -translate-y-1/2 rounded-full bg-[var(--primary-color)] px-4 py-1 text-sm font-semibold text-white">
                  Most Popular
                </p>
              )}
              <h3 className="text-2xl font-bold text-gray-800">{plan.name}</h3>
              <p className="mt-4 text-gray-600">{plan.description}</p>
              <p className="mt-6 flex items-baseline gap-1">
                <span className="text-5xl font-black tracking-tight text-gray-900">{plan.price}</span>
                <span className="text-lg font-semibold text-gray-600">{plan.period}</span>
              </p>
              <Button
                className={`mt-8 ${
                  plan.popular
                    ? "bg-[var(--primary-color)] hover:bg-[var(--primary-color)]/90 text-white"
                    : "bg-gray-100 hover:bg-gray-200 text-gray-800"
                }`}
              >
                {plan.name === "Growth"
                  ? "Start Growing"
                  : plan.name === "Enterprise"
                    ? "Contact Sales"
                    : "Get Started"}
              </Button>
              <ul className="mt-8 space-y-4 text-gray-600">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-[var(--primary-color)]">check_circle</span>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
