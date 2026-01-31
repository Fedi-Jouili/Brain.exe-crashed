import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Search, DollarSign, Sparkles } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-background">
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.15),transparent_50%)]" />
      </div>

      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8 lg:py-36">
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          {/* Left column - Text content */}
          <div className="flex flex-col gap-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary w-fit">
              <Sparkles className="h-4 w-4" />
              <span>AI-Powered Shopping Intelligence</span>
            </div>

            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl text-balance">
              Smart Shopping That{" "}
              <span className="text-primary">Understands Your Budget</span>
            </h1>

            <p className="text-lg text-muted-foreground leading-relaxed max-w-xl text-pretty">
              AI-powered product recommendations based on your real financial
              situation. Make informed purchase decisions with personalized
              affordability analysis.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row sm:gap-4 pt-2">
              <Button asChild size="lg" className="gap-2">
                <Link href="/profile">
                  Start Smart Shopping
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/about">Learn How It Works</Link>
              </Button>
            </div>

            {/* Trust indicators */}
            <div className="flex items-center gap-6 pt-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success" />
                <span>Real-time analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success" />
                <span>Privacy-first</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success" />
                <span>No credit check</span>
              </div>
            </div>
          </div>

          {/* Right column - Visual showcase */}
          <div className="relative">
            <div className="relative rounded-2xl border border-border bg-card p-6 shadow-xl">
              {/* Mock search interface */}
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
                  <Search className="h-5 w-5 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    laptop for programming...
                  </span>
                </div>

                {/* Mock result card */}
                <div className="rounded-lg border border-border bg-background p-4">
                  <div className="flex gap-4">
                    <div className="h-20 w-20 rounded-lg bg-muted flex items-center justify-center">
                      <span className="text-2xl text-muted-foreground">
                        {"{"}img{"}"}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold">MacBook Pro 14"</p>
                      <p className="text-lg font-bold text-primary">$1,999</p>
                      <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-success/10 px-2.5 py-1 text-xs font-medium text-success">
                        <div className="h-1.5 w-1.5 rounded-full bg-success" />
                        Affordable with financing
                      </div>
                    </div>
                  </div>
                </div>

                {/* Affordability preview */}
                <div className="rounded-lg border border-border bg-primary/5 p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                      <DollarSign className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        Affordability Analysis
                      </p>
                      <p className="text-xs text-muted-foreground">
                        12 months @ $167/mo - Within your budget
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Decorative badge */}
              <div className="absolute -right-3 -top-3 rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground shadow-lg">
                AI Powered
              </div>
            </div>

            {/* Decorative elements */}
            <div className="absolute -bottom-6 -left-6 h-24 w-24 rounded-full bg-accent/20 blur-2xl" />
            <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-primary/20 blur-2xl" />
          </div>
        </div>
      </div>
    </section>
  )
}
