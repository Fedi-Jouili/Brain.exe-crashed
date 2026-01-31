"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
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
  RefreshCcw,
} from "lucide-react"
import { useProfileStore, useRecentSearchStore } from "@/lib/store"
import { profileApi, APIError, NetworkError } from "@/lib/api"
import { ErrorState } from "@/components/ui/error-state"
import type { FinancialAnalysis } from "@/lib/types"

export default function DashboardPage() {
  const router = useRouter()
  const { profile, financialAnalysis, setFinancialAnalysis } = useProfileStore()
  const { searches } = useRecentSearchStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<{ type: "network" | "server" | "generic"; message?: string } | null>(null)

  // Fetch financial analysis from backend
  useEffect(() => {
    if (!profile) return

    const fetchAnalysis = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const analysis = await profileApi.getFinancialAnalysis()
        setFinancialAnalysis(analysis)
      } catch (err) {
        if (err instanceof NetworkError) {
          setError({ type: "network" })
        } else if (err instanceof APIError && err.status >= 500) {
          setError({ type: "server" })
        } else {
          // Use cached/local data if available, show warning
          setError({ type: "generic", message: "Using cached data" })
        }
      } finally {
        setIsLoading(false)
      }
    }

    fetchAnalysis()
  }, [profile, setFinancialAnalysis])

  const handleRetry = () => {
    setError(null)
    // Trigger refetch
    if (profile) {
      setIsLoading(true)
      profileApi
        .getFinancialAnalysis()
        .then(setFinancialAnalysis)
        .catch(() => setError({ type: "network" }))
        .finally(() => setIsLoading(false))
    }
  }

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

  const getCreditLabel = (rating: string | undefined) => {
    switch (rating) {
      case "excellent":
        return { label: "Excellent", color: "text-success" }
      case "very_good":
        return { label: "Very Good", color: "text-success" }
      case "good":
        return { label: "Good", color: "text-warning" }
      case "fair":
        return { label: "Fair", color: "text-warning" }
      case "poor":
        return { label: "Poor", color: "text-destructive" }
      default:
        return { label: "Unknown", color: "text-muted-foreground" }
    }
  }

  const creditLabel = getCreditLabel(financialAnalysis?.credit_rating)

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

          {/* Error State */}
          {error && error.type !== "generic" && (
            <div className="mb-8">
              <ErrorState
                type={error.type}
                onRetry={handleRetry}
              />
            </div>
          )}

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
                {isLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  <div
                    className={`text-2xl font-bold font-mono ${
                      (financialAnalysis?.disposable_income ?? 0) > 0
                        ? "text-success"
                        : "text-destructive"
                    }`}
                  >
                    ${(financialAnalysis?.disposable_income ?? profile.monthly_income - profile.monthly_expenses).toLocaleString()}
                  </div>
                )}
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
                {isLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  <div className="text-2xl font-bold font-mono text-primary">
                    ${(financialAnalysis?.safe_spending_limit ?? 0).toLocaleString()}
                  </div>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Per purchase ({profile.risk_tolerance || "medium"} risk)
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            {/* Financial Health */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Financial Health</CardTitle>
                    <CardDescription>
                      Key metrics that affect your affordability analysis
                    </CardDescription>
                  </div>
                  {!isLoading && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleRetry}
                      className="h-8 w-8"
                    >
                      <RefreshCcw className="h-4 w-4" />
                      <span className="sr-only">Refresh data</span>
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-6">
                {/* DTI Ratio */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Debt-to-Income Ratio</span>
                    </div>
                    {isLoading ? (
                      <Skeleton className="h-5 w-16" />
                    ) : (
                      <span
                        className={`text-sm font-mono font-medium ${
                          (financialAnalysis?.dti_ratio ?? 0) < 36
                            ? "text-success"
                            : (financialAnalysis?.dti_ratio ?? 0) < 43
                              ? "text-warning"
                              : "text-destructive"
                        }`}
                      >
                        {(financialAnalysis?.dti_ratio ?? 0).toFixed(1)}%
                      </span>
                    )}
                  </div>
                  {isLoading ? (
                    <Skeleton className="h-3 w-full" />
                  ) : (
                    <Progress
                      value={Math.min(financialAnalysis?.dti_ratio ?? 0, 100)}
                      className={`h-3 ${
                        (financialAnalysis?.dti_ratio ?? 0) < 36
                          ? "[&>div]:bg-success"
                          : (financialAnalysis?.dti_ratio ?? 0) < 43
                            ? "[&>div]:bg-warning"
                            : "[&>div]:bg-destructive"
                      }`}
                    />
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    {financialAnalysis?.dti_status === "healthy"
                      ? "Excellent! Your DTI is in a healthy range."
                      : financialAnalysis?.dti_status === "moderate"
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
                    {isLoading ? (
                      <Skeleton className="h-5 w-20" />
                    ) : (
                      <span
                        className={`text-sm font-mono font-medium ${
                          (financialAnalysis?.emergency_fund_months ?? 0) >= 3
                            ? "text-success"
                            : (financialAnalysis?.emergency_fund_months ?? 0) >= 1
                              ? "text-warning"
                              : "text-destructive"
                        }`}
                      >
                        {(financialAnalysis?.emergency_fund_months ?? 0).toFixed(1)} months
                      </span>
                    )}
                  </div>
                  {isLoading ? (
                    <Skeleton className="h-3 w-full" />
                  ) : (
                    <Progress
                      value={Math.min(
                        ((financialAnalysis?.emergency_fund_months ?? 0) / 6) * 100,
                        100
                      )}
                      className={`h-3 ${
                        (financialAnalysis?.emergency_fund_months ?? 0) >= 3
                          ? "[&>div]:bg-success"
                          : (financialAnalysis?.emergency_fund_months ?? 0) >= 1
                            ? "[&>div]:bg-warning"
                            : "[&>div]:bg-destructive"
                      }`}
                    />
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    {financialAnalysis?.emergency_fund_status === "excellent"
                      ? "Great! You have a solid emergency fund."
                      : financialAnalysis?.emergency_fund_status === "good"
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
                      {isLoading ? (
                        <Skeleton className="h-7 w-16 mx-auto mt-1" />
                      ) : (
                        <p className="text-lg font-bold font-mono text-success">
                          ${(financialAnalysis?.disposable_income ?? 0).toLocaleString()}
                        </p>
                      )}
                      <p className="text-xs text-success">
                        {financialAnalysis?.disposable_income
                          ? ((financialAnalysis.disposable_income / profile.monthly_income) * 100).toFixed(0)
                          : 0}
                        %
                      </p>
                    </div>
                  </div>
                </div>

                {/* Financing Eligibility */}
                {financialAnalysis && (
                  <>
                    <Separator />
                    <div className="flex items-center justify-between rounded-lg border border-border p-4">
                      <div className="flex items-center gap-3">
                        <CreditCard className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">Financing Eligibility</p>
                          <p className="text-xs text-muted-foreground">
                            Max monthly payment: $
                            {financialAnalysis.max_monthly_payment.toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          financialAnalysis.financing_eligible
                            ? "bg-success/10 text-success"
                            : "bg-destructive/10 text-destructive"
                        }`}
                      >
                        {financialAnalysis.financing_eligible ? "Eligible" : "Not Eligible"}
                      </div>
                    </div>
                  </>
                )}
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
                    <p className="text-sm text-muted-foreground">No recent searches</p>
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
