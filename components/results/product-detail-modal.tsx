"use client"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Star,
  ShoppingCart,
  Heart,
  Share2,
  Check,
  AlertTriangle,
  XCircle,
  CreditCard,
  PiggyBank,
  RefreshCcw,
  Shield,
  Bot,
  Package,
  Info,
} from "lucide-react"
import { useProfileStore } from "@/lib/store"
import { interactionApi } from "@/lib/api"
import type { Recommendation } from "@/lib/types"
import { cn } from "@/lib/utils"

interface ProductDetailModalProps {
  recommendation: Recommendation | null
  open: boolean
  onClose: () => void
}

export function ProductDetailModal({
  recommendation,
  open,
  onClose,
}: ProductDetailModalProps) {
  const { profile, financialAnalysis } = useProfileStore()

  if (!recommendation) return null

  const { product, affordability, explanation, scores, final_score } = recommendation

  const handlePurchase = async () => {
    if (!profile) return

    await interactionApi.track({
      user_id: profile.user_id,
      product_id: product.product_id,
      action: "purchase",
    })
  }

  const handleAddToCart = async () => {
    if (!profile) return

    await interactionApi.track({
      user_id: profile.user_id,
      product_id: product.product_id,
      action: "add_to_cart",
    })
  }

  const getAffordabilityInfo = () => {
    if (affordability.can_afford_cash) {
      return {
        icon: Check,
        color: "text-success",
        bgColor: "bg-success/10",
        borderColor: "border-success/20",
        title: "Affordable (Cash)",
        description:
          "You can purchase this product outright without impacting your financial health.",
      }
    }
    if (affordability.can_afford_financing) {
      return {
        icon: CreditCard,
        color: "text-warning",
        bgColor: "bg-warning/10",
        borderColor: "border-warning/20",
        title: "Affordable (Financing)",
        description:
          "This product is affordable with a financing plan. Monthly payments are within your budget.",
      }
    }
    return {
      icon: XCircle,
      color: "text-destructive",
      bgColor: "bg-destructive/10",
      borderColor: "border-destructive/20",
      title: "Currently Unaffordable",
      description:
        "This product exceeds your safe spending limit. Consider alternatives or saving up.",
    }
  }

  const affordabilityInfo = getAffordabilityInfo()
  const AffordabilityIcon = affordabilityInfo.icon

  const getRiskIndicator = () => {
    switch (affordability.risk_level) {
      case "safe":
        return { color: "bg-success", label: "Safe", icon: Check }
      case "caution":
        return { color: "bg-warning", label: "Caution", icon: AlertTriangle }
      case "risky":
        return { color: "bg-destructive", label: "Risky", icon: XCircle }
      default:
        return { color: "bg-muted", label: "Unknown", icon: AlertTriangle }
    }
  }

  const riskIndicator = getRiskIndicator()

  // Use backend-calculated values
  const monthlyPayment = affordability.monthly_payment || 0
  const ptiRatio = affordability.pti_ratio || 0
  const dtiImpact = affordability.dti_impact || 0

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-0">
        <DialogHeader className="sr-only">
          <DialogTitle>{product.name}</DialogTitle>
        </DialogHeader>

        <div className="grid md:grid-cols-5 gap-0">
          {/* Left Column - Product Info */}
          <div className="md:col-span-3 p-6">
            {/* Product Image */}
            <div className="relative aspect-video rounded-lg bg-muted overflow-hidden mb-6">
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <Package className="h-16 w-16 text-muted-foreground" />
                </div>
              )}

              {/* Rank Badge */}
              <div className="absolute left-3 top-3 flex h-10 w-10 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background shadow-lg">
                #{recommendation.rank}
              </div>
            </div>

            {/* Product Details */}
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant="secondary">{product.category}</Badge>
              {product.in_stock !== undefined && (
                <Badge variant={product.in_stock ? "default" : "destructive"}>
                  {product.in_stock ? "In Stock" : "Out of Stock"}
                </Badge>
              )}
            </div>

            <h2 className="text-2xl font-bold text-foreground mb-2">
              {product.name}
            </h2>

            <div className="flex items-center gap-4 mb-4">
              <span className="text-3xl font-bold text-foreground font-mono">
                ${product.price.toLocaleString()}
              </span>
              <div className="flex items-center gap-1">
                <Star className="h-5 w-5 fill-warning text-warning" />
                <span className="font-semibold">{product.rating.toFixed(1)}</span>
                {product.reviews_count && (
                  <span className="text-muted-foreground">
                    ({product.reviews_count.toLocaleString()} reviews)
                  </span>
                )}
              </div>
            </div>

            {product.description && (
              <p className="text-muted-foreground leading-relaxed mb-6">
                {product.description}
              </p>
            )}

            <Separator className="my-6" />

            {/* AI Explanation */}
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-3">
                <Bot className="h-5 w-5 text-primary" />
                <h3 className="font-semibold">Why We Recommend This</h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                {explanation.text}
              </p>

              {/* Key Factors */}
              {explanation.key_factors && explanation.key_factors.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {explanation.key_factors.map((factor, idx) => (
                    <span
                      key={idx}
                      className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4 mt-4 text-xs">
                <div className="flex items-center gap-1.5">
                  {explanation.verified ? (
                    <Check className="h-3.5 w-3.5 text-success" />
                  ) : (
                    <AlertTriangle className="h-3.5 w-3.5 text-warning" />
                  )}
                  <span>
                    {explanation.verified ? "Facts Verified" : "AI Generated"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5 text-primary" />
                  <span>Trust Score: {Math.round(explanation.trust * 100)}%</span>
                </div>
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="mt-6">
              <h3 className="font-semibold mb-4">Score Breakdown</h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-lg border border-border p-3 text-center">
                  <div className="text-2xl font-bold text-primary font-mono">
                    {Math.round(final_score)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">Overall</div>
                </div>
                <div className="rounded-lg border border-border p-3 text-center">
                  <div className="text-2xl font-bold font-mono">
                    {scores.thompson.toFixed(0)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">Thompson</div>
                </div>
                <div className="rounded-lg border border-border p-3 text-center">
                  <div className="text-2xl font-bold font-mono">
                    {Math.round(scores.financial * 100)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">Financial</div>
                </div>
                <div className="rounded-lg border border-border p-3 text-center">
                  <div className="text-2xl font-bold font-mono">
                    {scores.ragas.toFixed(0)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">RAGAS</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Affordability Panel */}
          <div className="md:col-span-2 border-t md:border-t-0 md:border-l border-border bg-muted/30 p-6 flex flex-col">
            {/* Affordability Badge */}
            <div
              className={cn(
                "rounded-lg border p-4 mb-6",
                affordabilityInfo.bgColor,
                affordabilityInfo.borderColor
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full",
                    affordabilityInfo.bgColor
                  )}
                >
                  <AffordabilityIcon
                    className={cn("h-5 w-5", affordabilityInfo.color)}
                  />
                </div>
                <div>
                  <p className={cn("font-semibold", affordabilityInfo.color)}>
                    {affordabilityInfo.title}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {affordabilityInfo.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Financial Metrics (from backend) */}
            {profile && (
              <div className="flex flex-col gap-4 mb-6">
                {/* DTI Impact */}
                {dtiImpact > 0 && (
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">DTI Impact</span>
                      <span className="font-medium font-mono">
                        +{dtiImpact.toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={Math.min(dtiImpact * 2, 100)}
                      className={cn(
                        "h-2",
                        dtiImpact < 5
                          ? "[&>div]:bg-success"
                          : dtiImpact < 10
                            ? "[&>div]:bg-warning"
                            : "[&>div]:bg-destructive"
                      )}
                    />
                  </div>
                )}

                {/* Monthly Payment */}
                {monthlyPayment > 0 && (
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">Monthly Payment</span>
                      <span className="font-medium font-mono">
                        ${monthlyPayment.toLocaleString()}/mo
                      </span>
                    </div>
                    <Progress
                      value={Math.min(ptiRatio, 100)}
                      className={cn(
                        "h-2",
                        ptiRatio < 20
                          ? "[&>div]:bg-success"
                          : ptiRatio < 30
                            ? "[&>div]:bg-warning"
                            : "[&>div]:bg-destructive"
                      )}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      {ptiRatio.toFixed(1)}% of disposable income
                    </p>
                  </div>
                )}

                {/* Risk Level */}
                <div className="flex items-center justify-between rounded-lg border border-border bg-card p-3">
                  <span className="text-sm text-muted-foreground">Risk Level</span>
                  <div className="flex items-center gap-2">
                    <div
                      className={cn("h-3 w-3 rounded-full", riskIndicator.color)}
                    />
                    <span className="text-sm font-medium">{riskIndicator.label}</span>
                  </div>
                </div>

                {/* Emergency Fund Impact */}
                {affordability.emergency_fund_impact !== undefined && (
                  <div className="flex items-start gap-2 rounded-lg border border-border bg-card p-3">
                    <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="text-xs text-muted-foreground">
                      {affordability.emergency_fund_impact > 50
                        ? "This purchase would significantly impact your emergency fund"
                        : affordability.emergency_fund_impact > 20
                          ? "This purchase would moderately impact your emergency fund"
                          : "Minimal impact on your emergency fund"}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* No Profile Warning */}
            {!profile && (
              <div className="flex items-start gap-3 rounded-lg border border-warning/50 bg-warning/10 p-4 mb-6">
                <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-foreground">
                    Limited Analysis
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Complete your financial profile to see personalized
                    affordability metrics.
                  </p>
                </div>
              </div>
            )}

            {/* Financing Options */}
            {!affordability.can_afford_cash && (
              <div className="mb-6">
                <h4 className="font-medium mb-3">Ways to Afford This</h4>
                <div className="flex flex-col gap-2">
                  <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-3">
                    <PiggyBank className="h-5 w-5 text-success mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">Save Monthly</p>
                      <p className="text-xs text-muted-foreground">
                        Save ${Math.round(product.price / 6).toLocaleString()}/month
                        for 6 months
                      </p>
                    </div>
                  </div>

                  {affordability.can_afford_financing && (
                    <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-3">
                      <CreditCard className="h-5 w-5 text-warning mt-0.5" />
                      <div>
                        <p className="text-sm font-medium">Financing Plan</p>
                        <p className="text-xs text-muted-foreground">
                          {affordability.financing_months || 12} months @{" "}
                          ${monthlyPayment}/mo
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-3">
                    <RefreshCcw className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">See Alternatives</p>
                      <p className="text-xs text-muted-foreground">
                        Find similar products in your budget
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-auto flex flex-col gap-3">
              <Button
                size="lg"
                className="w-full gap-2"
                disabled={
                  !affordability.can_afford_cash && !affordability.can_afford_financing
                }
                onClick={handleAddToCart}
              >
                <ShoppingCart className="h-5 w-5" />
                {affordability.can_afford_cash
                  ? "Add to Cart"
                  : affordability.can_afford_financing
                    ? "Start Financing"
                    : "Currently Unavailable"}
              </Button>

              <div className="grid grid-cols-2 gap-2">
                <Button variant="outline" className="gap-2">
                  <Heart className="h-4 w-4" />
                  Save
                </Button>
                <Button variant="outline" className="gap-2">
                  <Share2 className="h-4 w-4" />
                  Share
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
