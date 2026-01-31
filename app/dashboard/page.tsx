"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  DollarSign,
  CreditCard,
  PiggyBank,
  TrendingUp,
  Edit,
  Search,
  User,
  BarChart3,
  Wallet,
  ShieldCheck,
} from "lucide-react"
import {
  useProfileStore,
  useRecentSearchStore,
  calculateDisposableIncome,
  calculateDTI,
  calculateSafeSpendingLimit,
} from "@/lib/store"

export default function DashboardPage() {
  const router = useRouter()
  const { profile } = useProfileStore()
  const { searches } = useRecentSearchStore()

  if (!profile) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center bg-background">
          <div className="text-center px-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mx-auto mb-4">
              <User className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              No Profile Found
            </h2>
            <p className="mt-2 text-muted-foreground max-w-sm">
              Create your financial profile to access your personalized dashboard
            </p>
            <Button asChild className="mt-6">
              <Link href="/profile">Create Profile</Link>
            </Button>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  const disposableIncome = calculateDisposableIncome(profile)
  const dti = calculateDTI(profile)
  const safeSpendingLimit = calculateSafeSpendingLimit(profile)
  const savingsMonths = profile.monthly_expenses > 0 
    ? (profile.savings / profile.monthly_expenses).toFixed(1) 
    : 0

  const getCreditScoreLabel = (score: number) => {
    if (score >= 800) return { label: "Excellent", color: "text-success" }
    if (score >= 740) return { label: "Very Good", color: "text-success" }
    if (score >= 670) return { label: "Good", color: "text-warning" }
    if (score >= 580) return { label: "Fair", color: "text-warning" }
    return { label: "Poor", color: "text-destructive" }
  }

  const creditLabel = getCreditScoreLabel(profile.credit_score)

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
                Dashboard
              </h1>
              <p className="mt-1 text-muted-foreground">
                Your financial overview and shopping insights
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" asChild className="gap-2">
                <Link href="/profile">
                  <Edit className="h-4 w-4" />
                  Edit Profile
                </Link>
              </Button>
              <Button asChild className="gap-2">
                <Link href="/search">
                  <Search className="h-4 w-4" />
                  New Search
                </Link>
              </Button>
            </div>
          </div>

          {/* Profile Summary Cards */}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Monthly Income
                </CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono">
                  ${profile.monthly_income.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Gross monthly income
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Disposable Income
                </CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold font-mono ${disposableIncome > 0 ? "text-success" : "text-destructive"}`}>
                  ${disposableIncome.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  After expenses
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Credit Score
                </CardTitle>
                <CreditCard className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold font-mono ${creditLabel.color}`}>
                  {profile.credit_score}
                </div>
                <p className={`text-xs mt-1 ${creditLabel.color}`}>
                  {creditLabel.label}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Safe Spending Limit
                </CardTitle>
                <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono text-primary">
                  ${safeSpendingLimit.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Per purchase ({profile.risk_tolerance} risk)
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            {/* Financial Health */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Financial Health</CardTitle>
                <CardDescription>
                  Key metrics that affect your affordability analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-6">
                {/* DTI Ratio */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Debt-to-Income Ratio</span>
                    </div>
                    <span className={`text-sm font-mono font-medium ${dti < 36 ? "text-success" : dti < 43 ? "text-warning" : "text-destructive"}`}>
                      {dti.toFixed(1)}%
                    </span>
                  </div>
                  <Progress
                    value={Math.min(dti, 100)}
                    className={`h-3 ${dti < 36 ? "[&>div]:bg-success" : dti < 43 ? "[&>div]:bg-warning" : "[&>div]:bg-destructive"}`}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    {dti < 36
                      ? "Excellent! Your DTI is in a healthy range."
                      : dti < 43
                        ? "Good, but consider paying down debt."
                        : "High DTI may limit financing options."}
                  </p>
                </div>

                <Separator />

                {/* Emergency Fund */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <PiggyBank className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Emergency Fund</span>
                    </div>
                    <span className={`text-sm font-mono font-medium ${Number(savingsMonths) >= 3 ? "text-success" : Number(savingsMonths) >= 1 ? "text-warning" : "text-destructive"}`}>
                      {savingsMonths} months
                    </span>
                  </div>
                  <Progress
                    value={Math.min((Number(savingsMonths) / 6) * 100, 100)}
                    className={`h-3 ${Number(savingsMonths) >= 3 ? "[&>div]:bg-success" : Number(savingsMonths) >= 1 ? "[&>div]:bg-warning" : "[&>div]:bg-destructive"}`}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    {Number(savingsMonths) >= 6
                      ? "Great! You have a solid emergency fund."
                      : Number(savingsMonths) >= 3
                        ? "Good start! Aim for 6 months of expenses."
                        : "Consider building your emergency fund."}
                  </p>
                </div>

                <Separator />

                {/* Budget Breakdown */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Monthly Budget Breakdown</span>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="rounded-lg bg-muted p-3 text-center">
                      <p className="text-xs text-muted-foreground">Expenses</p>
                      <p className="text-lg font-bold font-mono">
                        ${profile.monthly_expenses.toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {((profile.monthly_expenses / profile.monthly_income) * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="rounded-lg bg-muted p-3 text-center">
                      <p className="text-xs text-muted-foreground">Debt Payments</p>
                      <p className="text-lg font-bold font-mono">
                        ${Math.round(profile.current_debt * 0.02).toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground">Est. monthly</p>
                    </div>
                    <div className="rounded-lg bg-success/10 p-3 text-center">
                      <p className="text-xs text-success">Available</p>
                      <p className="text-lg font-bold font-mono text-success">
                        ${disposableIncome.toLocaleString()}
                      </p>
                      <p className="text-xs text-success">
                        {((disposableIncome / profile.monthly_income) * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your recent searches and preferences</CardDescription>
              </CardHeader>
              <CardContent>
                {searches.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Recent Searches
                    </p>
                    {searches.map((search, index) => (
                      <button
                        key={index}
                        onClick={() => router.push("/search")}
                        className="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted/50"
                      >
                        <Search className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm truncate">{search}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Search className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                      No recent searches
                    </p>
                    <Button
                      variant="link"
                      className="mt-2"
                      onClick={() => router.push("/search")}
                    >
                      Start searching
                    </Button>
                  </div>
                )}

                <Separator className="my-6" />

                {/* Preferences */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
                    Your Preferences
                  </p>
                  <div className="flex flex-col gap-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Risk Tolerance</span>
                      <span className="font-medium capitalize">
                        {profile.risk_tolerance || "Medium"}
                      </span>
                    </div>
                    {profile.preferred_categories &&
                      profile.preferred_categories.length > 0 && (
                        <div>
                          <span className="text-muted-foreground">Categories</span>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {profile.preferred_categories.map((cat) => (
                              <span
                                key={cat}
                                className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                              >
                                {cat}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}
