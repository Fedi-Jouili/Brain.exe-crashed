import { UserPlus, Search, CheckCircle } from "lucide-react"

const steps = [
  {
    step: "01",
    icon: UserPlus,
    title: "Tell us your budget",
    description:
      "Create your financial profile in 2 minutes. Enter your income, expenses, and credit score for personalized results.",
    visual: "profile",
  },
  {
    step: "02",
    icon: Search,
    title: "Search products",
    description:
      "Search using text descriptions or upload an image. Our AI understands exactly what you're looking for.",
    visual: "search",
  },
  {
    step: "03",
    icon: CheckCircle,
    title: "Get smart recommendations",
    description:
      "Receive personalized product recommendations with affordability analysis and AI explanations for each option.",
    visual: "results",
  },
]

export function HowItWorksSection() {
  return (
    <section className="bg-background py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold text-primary">How It Works</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl text-balance">
            Three simple steps to smarter shopping
          </h2>
          <p className="mt-4 text-lg text-muted-foreground text-pretty">
            Our AI does the heavy lifting so you can focus on what matters -
            finding the perfect product within your budget.
          </p>
        </div>

        <div className="mt-16">
          <div className="relative">
            {/* Connection line - hidden on mobile */}
            <div className="absolute left-0 right-0 top-16 hidden h-0.5 bg-border lg:block" />

            <div className="grid gap-12 lg:grid-cols-3 lg:gap-8">
              {steps.map((step, index) => (
                <div key={step.step} className="relative flex flex-col items-center text-center">
                  {/* Step number with icon */}
                  <div className="relative z-10 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg">
                    <step.icon className="h-7 w-7" />
                  </div>

                  {/* Step indicator */}
                  <div className="mt-6 inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
                    Step {step.step}
                  </div>

                  <h3 className="mt-4 text-xl font-semibold text-foreground">
                    {step.title}
                  </h3>
                  <p className="mt-3 text-muted-foreground leading-relaxed max-w-xs">
                    {step.description}
                  </p>

                  {/* Visual representation */}
                  <div className="mt-8 w-full rounded-xl border border-border bg-card p-4 shadow-sm">
                    {step.visual === "profile" && (
                      <div className="flex flex-col gap-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Monthly Income</span>
                          <span className="font-medium">$5,000</span>
                        </div>
                        <div className="h-2 rounded-full bg-muted">
                          <div className="h-2 w-3/4 rounded-full bg-primary" />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Credit Score</span>
                          <span className="font-medium text-success">720</span>
                        </div>
                      </div>
                    )}
                    {step.visual === "search" && (
                      <div className="flex flex-col gap-3">
                        <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm text-muted-foreground">
                          <Search className="h-4 w-4" />
                          <span>gaming laptop under $1500</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="rounded-full bg-muted px-2 py-1 text-xs">Electronics</span>
                          <span className="rounded-full bg-muted px-2 py-1 text-xs">$500-$1500</span>
                        </div>
                      </div>
                    )}
                    {step.visual === "results" && (
                      <div className="flex flex-col gap-2">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="flex items-center gap-3 rounded-lg bg-background p-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted text-xs font-bold">
                              #{i}
                            </div>
                            <div className="flex-1">
                              <div className="h-2 w-20 rounded bg-muted" />
                            </div>
                            <div className={`h-2 w-2 rounded-full ${i === 1 ? "bg-success" : i === 2 ? "bg-warning" : "bg-muted"}`} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
