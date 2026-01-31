"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Star,
  Eye,
  ShoppingCart,
  CreditCard,
  ChevronDown,
  Lightbulb,
  Check,
  Package,
} from "lucide-react"
import { useProfileStore } from "@/lib/store"
import { api } from "@/lib/api"
import type { Recommendation } from "@/lib/types"
import { cn } from "@/lib/utils"

interface ProductCardProps {
  recommendation: Recommendation
  rank: number
  onClick: () => void
}

export function ProductCard({ recommendation, rank, onClick }: ProductCardProps) {
  const { profile } = useProfileStore()
  const [scoresOpen, setScoresOpen] = useState(false)
  const [tracked, setTracked] = useState(false)

  const { product, affordability, explanation, scores, final_score } = recommendation

  const handleTrackInteraction = async (action: "view" | "click" | "add_to_cart") => {
    if (!profile) return

    try {
      await api.trackInteraction({
        user_id: profile.user_id,
        product_id: product.product_id,
        action,
      })
      setTracked(true)
      setTimeout(() => setTracked(false), 2000)
    } catch {
      // Silent fail for tracking
    }
  }

  const getAffordabilityBadge = () => {
    if (affordability.can_afford_cash) {
      return {
        className: "bg-success/10 text-success border-success/20",
        icon: Check,
        text: "Affordable (Cash)",
        description: "You can buy this outright",
      }
    }
    if (affordability.can_afford_financing) {
      return {
        className: "bg-warning/10 text-warning border-warning/20",
        icon: CreditCard,
        text: "Affordable (Financing)",
        description: affordability.monthly_payment
          ? `${affordability.financing_months || 12} months @ $${affordability.monthly_payment}/mo`
          : "Available with payment plan",
      }
    }
    return {
      className: "bg-destructive/10 text-destructive border-destructive/20",
      icon: Package,
      text: "Currently Unaffordable",
      description: "Above your safe spending limit",
    }
  }

  const affordabilityBadge = getAffordabilityBadge()
  const AffordabilityIcon = affordabilityBadge.icon

  const getRiskColor = (level: string) => {
    switch (level) {
      case "safe":
        return "text-success"
      case "caution":
        return "text-warning"
      case "risky":
        return "text-destructive"
      default:
        return "text-muted-foreground"
    }
  }

  return (
    <Card className="group relative overflow-hidden transition-all hover:shadow-lg">
      {/* Rank Badge */}
      <div className="absolute left-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-foreground text-sm font-bold text-background shadow-md">
        #{rank}
      </div>

      {/* Tracked Toast */}
      {tracked && (
        <div className="absolute right-3 top-3 z-10 animate-in fade-in slide-in-from-top-2 rounded-full bg-success px-3 py-1 text-xs font-medium text-success-foreground shadow-md">
          Tracked
        </div>
      )}

      <CardContent className="p-0">
        {/* Product Image */}
        <div
          className="relative aspect-[4/3] cursor-pointer bg-muted"
          onClick={() => {
            handleTrackInteraction("view")
            onClick()
          }}
        >
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <Package className="h-12 w-12 text-muted-foreground" />
            </div>
          )}

          {/* Stock Status */}
          {product.in_stock !== undefined && (
            <div
              className={cn(
                "absolute bottom-2 right-2 rounded-full px-2 py-0.5 text-xs font-medium",
                product.in_stock
                  ? "bg-success/90 text-success-foreground"
                  : "bg-destructive/90 text-destructive-foreground"
              )}
            >
              {product.in_stock ? "In Stock" : "Out of Stock"}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex flex-col gap-3 p-4">
          {/* Product Info */}
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              {product.category}
            </span>
            <h3
              className="mt-1 font-semibold text-foreground line-clamp-2 cursor-pointer hover:text-primary transition-colors"
              onClick={() => {
                handleTrackInteraction("click")
                onClick()
              }}
            >
              {product.name}
            </h3>
          </div>

          {/* Price & Rating */}
          <div className="flex items-center justify-between">
            <span className="text-xl font-bold text-foreground font-mono">
              ${product.price.toLocaleString()}
            </span>
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4 fill-warning text-warning" />
              <span className="text-sm font-medium">{product.rating.toFixed(1)}</span>
              {product.reviews_count && (
                <span className="text-xs text-muted-foreground">
                  ({product.reviews_count.toLocaleString()})
                </span>
              )}
            </div>
          </div>

          {/* Affordability Badge */}
          <div
            className={cn(
              "flex items-start gap-3 rounded-lg border p-3",
              affordabilityBadge.className
            )}
          >
            <AffordabilityIcon className="h-5 w-5 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium">{affordabilityBadge.text}</p>
              <p className="text-xs opacity-80">{affordabilityBadge.description}</p>
            </div>
          </div>

          {/* Score Breakdown */}
          <Collapsible open={scoresOpen} onOpenChange={setScoresOpen}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full justify-between h-auto py-2 px-0 text-sm text-muted-foreground hover:text-foreground"
              >
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                    <span className="text-xs font-bold text-primary">
                      {Math.round(final_score)}
                    </span>
                  </div>
                  <span>Overall Score</span>
                </div>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    scoresOpen && "rotate-180"
                  )}
                />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="rounded-lg bg-muted p-2 text-center">
                  <p className="text-muted-foreground">Thompson</p>
                  <p className="font-mono font-semibold">{scores.thompson.toFixed(1)}</p>
                </div>
                <div className="rounded-lg bg-muted p-2 text-center">
                  <p className="text-muted-foreground">Financial</p>
                  <p className="font-mono font-semibold">
                    {(scores.financial * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="rounded-lg bg-muted p-2 text-center">
                  <p className="text-muted-foreground">RAGAS</p>
                  <p className="font-mono font-semibold">{scores.ragas.toFixed(1)}</p>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* AI Explanation Preview */}
          <div className="flex items-start gap-2 rounded-lg bg-muted/50 p-3">
            <Lightbulb className="h-4 w-4 shrink-0 text-primary mt-0.5" />
            <div className="text-xs text-muted-foreground line-clamp-2">
              {explanation.text}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-2 pt-2">
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => {
                handleTrackInteraction("view")
                onClick()
              }}
            >
              <Eye className="h-4 w-4" />
              Details
            </Button>
            <Button
              className="gap-2"
              disabled={!affordability.can_afford_cash && !affordability.can_afford_financing}
              onClick={() => handleTrackInteraction("add_to_cart")}
            >
              <ShoppingCart className="h-4 w-4" />
              Add to Cart
            </Button>
          </div>

          {/* Financing Link */}
          {!affordability.can_afford_cash && affordability.can_afford_financing && (
            <Button
              variant="link"
              className="h-auto p-0 text-xs text-warning justify-start"
              onClick={onClick}
            >
              See Financing Options
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
