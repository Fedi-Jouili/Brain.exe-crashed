import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  ArrowRight,
  Search,
  DollarSign,
  Brain,
  Shield,
  Zap,
  Bot,
  Database,
  GitBranch,
  UserPlus,
  CheckCircle,
  Lock,
  Eye,
  Server,
} from "lucide-react"

const steps = [
  {
    icon: UserPlus,
    title: "Create Your Profile",
    description:
      "Enter your financial information including income, expenses, credit score, and savings. This takes about 2 minutes and helps us provide personalized recommendations.",
  },
  {
    icon: Search,
    title: "Search for Products",
    description:
      "Use text descriptions or upload images to find products. Our CLIP-powered AI understands natural language and visual similarity to find exactly what you're looking for.",
  },
  {
    icon: Brain,
    title: "AI Analyzes Options",
    description:
      "Our 5-agent system evaluates products using Thompson Sampling, financial analysis, and semantic search to rank recommendations based on your unique situation.",
  },
  {
    icon: CheckCircle,
    title: "Get Smart Recommendations",
    description:
      "Receive personalized product recommendations with affordability analysis, financing options, and transparent AI explanations for each suggestion.",
  },
]

const agents = [
  {
    name: "Router Agent",
    description: "Determines query complexity and routes to the appropriate analysis path (FAST, SMART, or DEEP).",
    color: "bg-primary",
  },
  {
    name: "Search Agent",
    description: "Uses CLIP multimodal embeddings and Qdrant vector search to find relevant products.",
    color: "bg-accent",
  },
  {
    name: "Financial Agent",
    description: "Analyzes your financial profile to determine affordability using DTI, PTI, and emergency fund metrics.",
    color: "bg-success",
  },
  {
    name: "Recommendation Agent",
    description: "Applies Thompson Sampling reinforcement learning to personalize rankings based on your interactions.",
    color: "bg-warning",
  },
  {
    name: "Explanation Agent",
    description: "Uses Gemini 2.0 Flash to generate human-readable explanations for each recommendation.",
    color: "bg-chart-5",
  },
]

const privacyPoints = [
  {
    icon: Lock,
    title: "Data Encryption",
    description: "All financial data is encrypted in transit and at rest using industry-standard protocols.",
  },
  {
    icon: Eye,
    title: "No Third-Party Sharing",
    description: "We never sell or share your personal information with advertisers or data brokers.",
  },
  {
    icon: Server,
    title: "Local Analysis",
    description: "Financial calculations happen securely without exposing raw data to external services.",
  },
  {
    icon: Shield,
    title: "No Credit Checks",
    description: "We never perform hard credit inquiries that could affect your credit score.",
  },
]

const faqs = [
  {
    question: "How accurate is the affordability analysis?",
    answer:
      "Our affordability analysis uses standard financial metrics including Debt-to-Income (DTI) ratio, Payment-to-Income (PTI) ratio, and emergency fund considerations. While these provide reliable guidance, they should be used alongside your own financial judgment and professional advice for major purchases.",
  },
  {
    question: "What is Thompson Sampling?",
    answer:
      "Thompson Sampling is a reinforcement learning algorithm that balances exploration and exploitation. It learns from your interactions (views, clicks, purchases) to personalize recommendations over time, showing you products you're more likely to find valuable while still discovering new options.",
  },
  {
    question: "How does image search work?",
    answer:
      "We use CLIP (Contrastive Language-Image Pre-training) to create embeddings that understand both text and images. When you upload an image, we find products with similar visual features in our vector database, allowing you to find items that match a style you like.",
  },
  {
    question: "What do the complexity levels (FAST/SMART/DEEP) mean?",
    answer:
      "FAST queries are simple searches that can be answered quickly from cache. SMART queries require AI analysis but don't need deep financial calculations. DEEP queries involve comprehensive financial analysis, personalized scoring, and detailed explanations.",
  },
  {
    question: "Can I use this without creating a profile?",
    answer:
      "Yes, you can search for products without a profile, but you won't see personalized affordability analysis. Creating a profile takes just 2 minutes and significantly improves the relevance of your recommendations.",
  },
  {
    question: "How do you determine what's 'affordable'?",
    answer:
      "We analyze three key factors: DTI ratio (should be under 43%), the impact on your monthly budget (payment shouldn't exceed 20-30% of disposable income), and emergency fund preservation (maintaining at least 3 months of expenses). Products meeting these criteria are marked as affordable.",
  },
]

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        {/* Hero Section */}
        <section className="border-b border-border bg-card py-16 sm:py-24">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl text-balance">
              Smart Shopping with{" "}
              <span className="text-primary">Financial Intelligence</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto text-pretty">
              FinCommerce Engine combines cutting-edge AI with financial analysis
              to help you make informed purchase decisions. No more buyer's
              remorse - just smart, personalized recommendations.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button asChild size="lg" className="gap-2">
                <Link href="/profile">
                  Get Started
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/search">Try a Search</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
                How It Works
              </h2>
              <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
                From search to purchase, here's how FinCommerce Engine helps you
                shop smarter
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {steps.map((step, index) => (
                <div key={step.title} className="relative">
                  <div className="flex flex-col items-center text-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg mb-4">
                      <step.icon className="h-6 w-6" />
                    </div>
                    <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary mb-3">
                      Step {index + 1}
                    </span>
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      {step.title}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* AI Architecture */}
        <section className="border-t border-border bg-card py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary mb-4">
                <Bot className="h-4 w-4" />
                AI Transparency
              </div>
              <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
                Our Multi-Agent System
              </h2>
              <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
                Five specialized AI agents work together to provide you with the
                best recommendations
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {agents.map((agent) => (
                <Card key={agent.name}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`h-3 w-3 rounded-full ${agent.color}`}
                      />
                      <CardTitle className="text-base">{agent.name}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {agent.description}
                    </p>
                  </CardContent>
                </Card>
              ))}

              {/* Tech Stack Card */}
              <Card className="bg-muted/50">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-3">
                    <Database className="h-5 w-5 text-muted-foreground" />
                    <CardTitle className="text-base">Tech Stack</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "LangGraph",
                      "Gemini 2.0",
                      "CLIP",
                      "Qdrant",
                      "Redis",
                      "FastAPI",
                    ].map((tech) => (
                      <span
                        key={tech}
                        className="rounded-full bg-background border border-border px-2.5 py-0.5 text-xs font-medium"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Architecture Diagram */}
            <Card className="mt-8">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <GitBranch className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold">Query Flow</h3>
                </div>
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-primary/10 px-3 py-1 text-primary font-medium">
                      Query
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-muted px-3 py-1">Router</div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-muted px-3 py-1">Search</div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-muted px-3 py-1">Financial</div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-muted px-3 py-1">Ranking</div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="rounded-full bg-success/10 px-3 py-1 text-success font-medium">
                    Results
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Privacy & Security */}
        <section className="py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 rounded-full bg-success/10 px-4 py-1.5 text-sm font-medium text-success mb-4">
                <Shield className="h-4 w-4" />
                Privacy First
              </div>
              <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
                Your Data Stays Private
              </h2>
              <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
                We take your financial privacy seriously. Here's how we protect
                your information.
              </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {privacyPoints.map((point) => (
                <Card key={point.title}>
                  <CardContent className="pt-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-success/10 text-success mb-4">
                      <point.icon className="h-6 w-6" />
                    </div>
                    <h3 className="font-semibold text-foreground mb-2">
                      {point.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {point.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="border-t border-border bg-card py-16 sm:py-24">
          <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
                Frequently Asked Questions
              </h2>
              <p className="mt-3 text-muted-foreground">
                Everything you need to know about FinCommerce Engine
              </p>
            </div>

            <Accordion type="single" collapsible className="w-full">
              {faqs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`}>
                  <AccordionTrigger className="text-left">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 sm:py-24">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
              Ready to shop smarter?
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Join thousands of smart shoppers making informed purchase decisions
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button asChild size="lg" className="gap-2">
                <Link href="/profile">
                  Create Your Profile
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/search">Try Without Profile</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
