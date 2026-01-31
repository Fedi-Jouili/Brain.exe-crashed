import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Star, Users, TrendingUp, Shield } from "lucide-react"

const stats = [
  {
    icon: Users,
    value: "10,000+",
    label: "Smart Shoppers",
  },
  {
    icon: TrendingUp,
    value: "$2.4M",
    label: "Saved on Purchases",
  },
  {
    icon: Star,
    value: "4.9/5",
    label: "User Rating",
  },
  {
    icon: Shield,
    value: "100%",
    label: "Privacy Protected",
  },
]

const testimonials = [
  {
    quote:
      "Finally, a tool that tells me if I can actually afford something. No more buyer's remorse!",
    author: "Sarah M.",
    role: "Budget-Conscious Shopper",
    rating: 5,
  },
  {
    quote:
      "The AI explanations helped me understand why certain products were better for my situation.",
    author: "Marcus T.",
    role: "First-Time Buyer",
    rating: 5,
  },
  {
    quote:
      "Data-driven recommendations that actually make sense. This is how shopping should be.",
    author: "Jennifer K.",
    role: "Smart Shopper",
    rating: 5,
  },
]

export function SocialProofSection() {
  return (
    <section className="border-t border-border bg-card py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <stat.icon className="h-6 w-6 text-primary" />
              </div>
              <p className="mt-4 text-3xl font-bold text-foreground">
                {stat.value}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Testimonials */}
        <div className="mt-20">
          <h3 className="text-center text-2xl font-bold text-foreground">
            Trusted by smart shoppers
          </h3>
          <div className="mt-10 grid gap-8 md:grid-cols-3">
            {testimonials.map((testimonial) => (
              <div
                key={testimonial.author}
                className="rounded-xl border border-border bg-background p-6"
              >
                <div className="flex gap-1">
                  {Array.from({ length: testimonial.rating }).map((_, i) => (
                    <Star
                      key={i}
                      className="h-4 w-4 fill-warning text-warning"
                    />
                  ))}
                </div>
                <p className="mt-4 text-foreground leading-relaxed">
                  "{testimonial.quote}"
                </p>
                <div className="mt-6 border-t border-border pt-4">
                  <p className="font-medium text-foreground">
                    {testimonial.author}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {testimonial.role}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-20 rounded-2xl bg-primary/5 p-8 text-center sm:p-12">
          <h3 className="text-2xl font-bold text-foreground sm:text-3xl text-balance">
            Ready to shop smarter?
          </h3>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground text-pretty">
            Join thousands of smart shoppers who make informed purchase decisions
            with personalized affordability analysis.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button asChild size="lg" className="gap-2">
              <Link href="/profile">
                Get Started Free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/about">See How It Works</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
