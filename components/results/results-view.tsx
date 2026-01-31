"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ArrowLeft, Zap, Search } from "lucide-react"
import { useSearchStore } from "@/lib/store"
import { ProductCard } from "./product-card"
import { ProductDetailModal } from "./product-detail-modal"
import type { Recommendation } from "@/lib/types"

type SortOption = "score" | "price-low" | "price-high" | "affordability"

export function ResultsView() {
  const { results, query } = useSearchStore()
  const [sortBy, setSortBy] = useState<SortOption>("score")
  const [selectedProduct, setSelectedProduct] = useState<Recommendation | null>(null)
  const [sortedResults, setSortedResults] = useState<Recommendation[]>([])

  useEffect(() => {
    if (!results?.recommendations) return

    const sorted = [...results.recommendations]
    switch (sortBy) {
      case "price-low":
        sorted.sort((a, b) => a.product.price - b.product.price)
        break
      case "price-high":
        sorted.sort((a, b) => b.product.price - a.product.price)
        break
      case "affordability":
        sorted.sort((a, b) => {
          const aScore = a.affordability.can_afford_cash
            ? 2
            : a.affordability.can_afford_financing
              ? 1
              : 0
          const bScore = b.affordability.can_afford_cash
            ? 2
            : b.affordability.can_afford_financing
              ? 1
              : 0
          return bScore - aScore
        })
        break
      default:
        sorted.sort((a, b) => b.final_score - a.final_score)
    }
    setSortedResults(sorted)
  }, [results, sortBy])

  const affordableCount =
    results?.recommendations.filter(
      (r) => r.affordability.can_afford_cash || r.affordability.can_afford_financing
    ).length || 0

  const getComplexityBadge = (level: string) => {
    switch (level) {
      case "FAST":
        return { color: "bg-success/10 text-success border-success/20", label: "FAST Path" }
      case "SMART":
        return { color: "bg-warning/10 text-warning border-warning/20", label: "SMART Path" }
      case "DEEP":
        return { color: "bg-destructive/10 text-destructive border-destructive/20", label: "DEEP Path" }
      default:
        return { color: "bg-muted text-muted-foreground", label: level }
    }
  }

  if (!results) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">No results to display</h2>
          <p className="text-muted-foreground">
            Start a new search to see personalized recommendations
          </p>
          <Button asChild className="mt-4">
            <Link href="/search">New Search</Link>
          </Button>
        </div>
      </div>
    )
  }

  const complexityBadge = getComplexityBadge(results.metadata.complexity_level)

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <Button variant="ghost" asChild className="mb-4 gap-2 -ml-2">
          <Link href="/search">
            <ArrowLeft className="h-4 w-4" />
            Back to Search
          </Link>
        </Button>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Results for "{results.query}"
            </h1>
            <p className="mt-1 text-muted-foreground">
              {results.recommendations.length} recommendations found
            </p>
          </div>

          <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="score">Best Match</SelectItem>
              <SelectItem value="price-low">Price: Low to High</SelectItem>
              <SelectItem value="price-high">Price: High to Low</SelectItem>
              <SelectItem value="affordability">Affordability</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Metadata Banner */}
      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-4">
        <div className="flex items-center gap-2 text-sm">
          <Zap className="h-4 w-4 text-warning" />
          <span className="text-muted-foreground">Results in</span>
          <span className="font-mono font-medium">
            {(results.metadata.execution_time_ms / 1000).toFixed(2)}s
          </span>
        </div>

        <div className="h-4 w-px bg-border" />

        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${complexityBadge.color}`}
        >
          {complexityBadge.label}
        </span>

        <div className="h-4 w-px bg-border" />

        <span className="text-sm">
          <span className="text-success font-medium">{affordableCount}</span>
          <span className="text-muted-foreground"> affordable options</span>
        </span>

        {results.metadata.cache_hit && (
          <>
            <div className="h-4 w-px bg-border" />
            <span className="inline-flex items-center rounded-full bg-accent/10 border border-accent/20 px-2.5 py-0.5 text-xs font-medium text-accent">
              Cached
            </span>
          </>
        )}
      </div>

      {/* Results Grid */}
      {sortedResults.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sortedResults.map((recommendation, index) => (
            <ProductCard
              key={recommendation.product.product_id}
              recommendation={recommendation}
              rank={index + 1}
              onClick={() => setSelectedProduct(recommendation)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <p className="text-muted-foreground">No products match your criteria</p>
          <Button asChild variant="outline" className="mt-4">
            <Link href="/search">Try Different Search</Link>
          </Button>
        </div>
      )}

      {/* Product Detail Modal */}
      <ProductDetailModal
        recommendation={selectedProduct}
        open={!!selectedProduct}
        onClose={() => setSelectedProduct(null)}
      />
    </div>
  )
}
