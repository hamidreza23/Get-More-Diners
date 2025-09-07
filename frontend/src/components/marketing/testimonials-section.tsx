export function TestimonialsSection() {
  const testimonials = [
    {
      quote:
        "Get More Diners helped us reach 300+ new customers in our first month. The AI-powered offers really work!",
      author: "Maria Rodriguez",
      title: "Owner, Bella Vista Italian",
      avatar: "/restaurant-owner-woman.png",
    },
    {
      quote:
        "We've increased our weekend bookings by 40% using their targeted SMS campaigns. Game changer for our business.",
      author: "James Chen",
      title: "Manager, Dragon Palace Asian Cuisine",
      avatar: "/restaurant-manager-man.png",
    },
    {
      quote: "The search filters help us find exactly the right customers. Our conversion rate has never been higher.",
      author: "Sarah Thompson",
      title: "Owner, Farm Fresh Bistro",
      avatar: "/restaurant-owner-woman-chef.jpg",
    },
  ]

  return (
    <section className="py-20 lg:py-28 bg-gray-50">
      <div className="mx-auto max-w-6xl px-4">
        <div className="text-center">
          <h2 className="text-4xl font-bold tracking-tighter text-gray-800 sm:text-5xl">
            Loved by Restaurant Owners Everywhere
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            See how Get More Diners is helping restaurants grow their customer base.
          </p>
        </div>
        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {testimonials.map((testimonial, index) => (
            <div key={index} className="bg-white rounded-xl p-8 shadow-sm">
              <blockquote className="text-gray-700 mb-6">"{testimonial.quote}"</blockquote>
              <div className="flex items-center gap-4">
                <img
                  src={testimonial.avatar || "/placeholder.svg"}
                  alt={testimonial.author}
                  className="w-12 h-12 rounded-full"
                />
                <div>
                  <p className="font-semibold text-gray-900">{testimonial.author}</p>
                  <p className="text-sm text-gray-600">{testimonial.title}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

