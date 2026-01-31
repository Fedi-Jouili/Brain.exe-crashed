"use client"

import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Search,
  Upload,
  X,
  Clock,
  ChevronDown,
  Loader2,
  Sparkles,
  Image as ImageIcon,
} from "lucide-react"
import { useProfileStore, useSearchStore, useRecentSearchStore } from "@/lib/store"
import { api, APIError } from "@/lib/api"
import { PRODUCT_CATEGORIES } from "@/lib/types"

const budgetOptions = [
  { label: "Under $500", value: "0-500" },
  { label: "$500 - $1,000", value: "500-1000" },
  { label: "$1,000 - $2,000", value: "1000-2000" },
  { label: "Custom", value: "custom" },
]

export function SearchInterface() {
  const router = useRouter()
  const { profile } = useProfileStore()
  const { setResults, setLoading, setError, isLoading, error } = useSearchStore()
  const { searches, addSearch } = useRecentSearchStore()

  const [query, setQuery] = useState("")
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [selectedBudget, setSelectedBudget] = useState<string>("custom")
  const [priceRange, setPriceRange] = useState([0, 2000])
  const [category, setCategory] = useState<string>("all")
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [inStockOnly, setInStockOnly] = useState(false)
  const [financingAvailable, setFinancingAvailable] = useState(false)

  const handleImageUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        setImageFile(file)
        const reader = new FileReader()
        reader.onload = (e) => {
          setImagePreview(e.target?.result as string)
        }
        reader.readAsDataURL(file)
      }
    },
    []
  )

  const removeImage = () => {
    setImageFile(null)
    setImagePreview(null)
  }

  const handleBudgetSelect = (value: string) => {
    setSelectedBudget(value)
    if (value !== "custom") {
      const [min, max] = value.split("-").map(Number)
      setPriceRange([min, max])
    }
  }

  const handleSearch = async () => {
    if (!query.trim() && !imageFile) {
      setError("Please enter a search query or upload an image")
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Convert image to base64 if present
      let imageBase64: string | undefined
      if (imageFile) {
        const reader = new FileReader()
        imageBase64 = await new Promise((resolve) => {
          reader.onload = (e) => {
            const result = e.target?.result as string
            resolve(result.split(",")[1])
          }
          reader.readAsDataURL(imageFile)
        })
      }

      const results = await api.search({
        query: query.trim() || "similar products",
        user_profile: profile || undefined,
        max_results: 10,
        image_base64: imageBase64,
      })

      setResults(results)
      if (query.trim()) {
        addSearch(query.trim())
      }
      router.push("/results")
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("An unexpected error occurred. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRecentSearch = (searchQuery: string) => {
    setQuery(searchQuery)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleSearch()
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-foreground sm:text-4xl">
          What are you looking for?
        </h1>
        <p className="mt-3 text-lg text-muted-foreground">
          Search with text or upload an image to find products
        </p>
      </div>

      {/* Search Card */}
      <Card className="mb-8">
        <CardContent className="p-6">
          {/* Main Search Input */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="e.g., laptop for programming, gaming headphones, ergonomic chair..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="h-14 pl-12 pr-4 text-lg"
              disabled={isLoading}
            />
          </div>

          {/* Image Upload */}
          <div className="mt-4">
            {imagePreview ? (
              <div className="relative inline-flex items-center gap-4 rounded-lg border border-border bg-muted/50 p-3">
                <img
                  src={imagePreview}
                  alt="Uploaded preview"
                  className="h-16 w-16 rounded-md object-cover"
                />
                <div className="flex-1">
                  <p className="text-sm font-medium">Image uploaded</p>
                  <p className="text-xs text-muted-foreground">
                    {imageFile?.name}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={removeImage}
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Remove image</span>
                </Button>
              </div>
            ) : (
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-border p-4 transition-colors hover:bg-muted/50">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                  <ImageIcon className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium">
                    Upload an image to find similar products
                  </p>
                  <p className="text-xs text-muted-foreground">
                    PNG, JPG up to 10MB
                  </p>
                </div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="sr-only"
                  disabled={isLoading}
                />
              </label>
            )}
          </div>

          {/* Budget Quick Select */}
          <div className="mt-6">
            <Label className="text-sm font-medium">Quick Budget</Label>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {budgetOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleBudgetSelect(option.value)}
                  className={`rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors ${
                    selectedBudget === option.value
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border hover:bg-muted/50"
                  }`}
                  disabled={isLoading}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Advanced Filters */}
          <Collapsible open={filtersOpen} onOpenChange={setFiltersOpen}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="mt-4 w-full justify-between text-muted-foreground"
              >
                Advanced Filters
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${filtersOpen ? "rotate-180" : ""}`}
                />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-4">
              <div className="grid gap-6 sm:grid-cols-2">
                {/* Category */}
                <div className="flex flex-col gap-2">
                  <Label>Category</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      {PRODUCT_CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat.toLowerCase()}>
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Price Range */}
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <Label>Price Range</Label>
                    <span className="text-sm font-mono text-muted-foreground">
                      ${priceRange[0]} - ${priceRange[1]}
                    </span>
                  </div>
                  <Slider
                    value={priceRange}
                    onValueChange={setPriceRange}
                    min={0}
                    max={5000}
                    step={50}
                  />
                </div>

                {/* Toggles */}
                <div className="flex items-center justify-between">
                  <Label htmlFor="in-stock">In Stock Only</Label>
                  <Switch
                    id="in-stock"
                    checked={inStockOnly}
                    onCheckedChange={setInStockOnly}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="financing">Financing Available</Label>
                  <Switch
                    id="financing"
                    checked={financingAvailable}
                    onCheckedChange={setFinancingAvailable}
                  />
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* Error Message */}
          {error && (
            <div className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Search Button */}
          <Button
            onClick={handleSearch}
            disabled={isLoading || (!query.trim() && !imageFile)}
            className="mt-6 h-12 w-full gap-2 text-base"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                Find Smart Recommendations
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Recent Searches */}
      {searches.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
            <Clock className="h-4 w-4" />
            <span>Recent Searches</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {searches.map((search) => (
              <button
                key={search}
                onClick={() => handleRecentSearch(search)}
                className="rounded-full border border-border bg-card px-4 py-1.5 text-sm transition-colors hover:bg-muted hover:border-muted-foreground"
                disabled={isLoading}
              >
                {search}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Profile Status */}
      {!profile && (
        <Card className="border-warning/50 bg-warning/5">
          <CardContent className="flex items-start gap-4 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-warning/10">
              <Sparkles className="h-5 w-5 text-warning" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">
                Get personalized results
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Complete your profile to see affordability analysis and
                personalized recommendations.
              </p>
              <Button
                variant="link"
                className="mt-2 h-auto p-0 text-warning"
                onClick={() => router.push("/profile")}
              >
                Set up profile
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Suggestions */}
      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Try searching for:
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {[
            "laptop for programming",
            "wireless headphones",
            "standing desk",
            "4K monitor",
          ].map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => setQuery(suggestion)}
              className="text-sm text-primary hover:underline"
              disabled={isLoading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
