import { Search, DollarSign, Brain, ShieldCheck, Zap, LineChart } from "lucide-react"

const features = [
  {
    icon: Search,
    title: "Smart Discovery",
    description:
      "Find products using text or images. Our CLIP-powered multimodal search understands what you're looking for.",
    highlight: "Text + Image Search",
  },
  {
    icon: DollarSign,
    title: "Affordability Analysis",
    description:
      "Real-time budget checks based on your actual income, debt, and credit score. Know if you can truly afford it.",
    highlight: "DTI & PTI Analysis",
  },
  {
    icon: Brain,
    title: "AI Explanations",
    description:
      "Understand why each product is recommended. Transparent AI reasoning with no black boxes.",
    highlight: "Gemini 2.0 Powered",
  },
  {
    icon: LineChart,
    title: "Learning System",
    description:
      "Thompson Sampling reinforcement learning adapts to your preferences. Gets smarter with every search.",
    highlight: "Personalized Results",
  },
  {
    icon: ShieldCheck,
    title: "Privacy First",
    description:
      "Your financial data stays private. We analyze locally and never share your information with third parties.",
    highlight: "No Credit Checks",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description:
      "Results in under 3 seconds. Our multi-agent system routes queries intelligently for optimal speed.",
    highlight: "3s Response Time",
  },
]

export function FeaturesSection() {
  return (
    <section className="border-t border-border bg-card py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold text-primary">Features</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl text-balance">
            Everything you need to shop smarter
          </h2>
          <p className="mt-4 text-lg text-muted-foreground text-pretty">
            Combining cutting-edge AI with financial intelligence to help you
            make the best purchase decisions.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group relative rounded-xl border border-border bg-background p-6 transition-all hover:border-primary/50 hover:shadow-lg"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2 text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
              <div className="mt-4 inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {feature.highlight}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
