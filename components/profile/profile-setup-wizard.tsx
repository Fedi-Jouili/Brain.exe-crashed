"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { ArrowLeft, ArrowRight, Check, Shield, DollarSign, Settings } from "lucide-react"
import { useProfileStore, generateUserId, calculateDisposableIncome } from "@/lib/store"
import type { UserProfile } from "@/lib/types"
import { PRODUCT_CATEGORIES } from "@/lib/types"

type Step = 1 | 2 | 3

interface FormData {
  user_id: string
  monthly_income: number
  monthly_expenses: number
  credit_score: number
  current_debt: number
  savings: number
  risk_tolerance: "low" | "medium" | "high"
  preferred_categories: string[]
}

const stepInfo = [
  { icon: Shield, title: "Basic Info", description: "We keep this private" },
  { icon: DollarSign, title: "Financial Profile", description: "For personalized results" },
  { icon: Settings, title: "Preferences", description: "Customize your experience" },
]

export function ProfileSetupWizard() {
  const router = useRouter()
  const { profile, setProfile } = useProfileStore()
  const [step, setStep] = useState<Step>(1)
  const [formData, setFormData] = useState<FormData>({
    user_id: profile?.user_id || generateUserId(),
    monthly_income: profile?.monthly_income || 5000,
    monthly_expenses: profile?.monthly_expenses || 3000,
    credit_score: profile?.credit_score || 700,
    current_debt: profile?.current_debt || 0,
    savings: profile?.savings || 0,
    risk_tolerance: profile?.risk_tolerance || "medium",
    preferred_categories: profile?.preferred_categories || [],
  })

  const progress = (step / 3) * 100
  const disposableIncome = formData.monthly_income - formData.monthly_expenses

  const updateField = <K extends keyof FormData>(field: K, value: FormData[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleNext = () => {
    if (step < 3) {
      setStep((step + 1) as Step)
    } else {
      handleSave()
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep((step - 1) as Step)
    }
  }

  const handleSave = () => {
    const profileData: UserProfile = {
      user_id: formData.user_id,
      monthly_income: formData.monthly_income,
      monthly_expenses: formData.monthly_expenses,
      credit_score: formData.credit_score,
      current_debt: formData.current_debt,
      savings: formData.savings,
      risk_tolerance: formData.risk_tolerance,
      preferred_categories: formData.preferred_categories,
    }
    setProfile(profileData)
    router.push("/search")
  }

  const handleSkip = () => {
    router.push("/search")
  }

  const toggleCategory = (category: string) => {
    setFormData((prev) => ({
      ...prev,
      preferred_categories: prev.preferred_categories.includes(category)
        ? prev.preferred_categories.filter((c) => c !== category)
        : [...prev.preferred_categories, category],
    }))
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
          Set Up Your Profile
        </h1>
        <p className="mt-2 text-muted-foreground">
          Get personalized product recommendations based on your financial situation
        </p>
      </div>

      {/* Progress */}
      <div className="flex flex-col gap-4">
        <Progress value={progress} className="h-2" />
        <div className="flex justify-between">
          {stepInfo.map((info, index) => {
            const StepIcon = info.icon
            const isActive = step === index + 1
            const isComplete = step > index + 1
            return (
              <div
                key={info.title}
                className={`flex flex-col items-center gap-2 ${
                  isActive ? "text-primary" : isComplete ? "text-success" : "text-muted-foreground"
                }`}
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${
                    isActive
                      ? "border-primary bg-primary/10"
                      : isComplete
                        ? "border-success bg-success/10"
                        : "border-muted"
                  }`}
                >
                  {isComplete ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <StepIcon className="h-5 w-5" />
                  )}
                </div>
                <span className="hidden text-xs font-medium sm:block">
                  {info.title}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{stepInfo[step - 1].title}</CardTitle>
          <CardDescription>{stepInfo[step - 1].description}</CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-2">
                <Label htmlFor="user_id">User ID</Label>
                <Input
                  id="user_id"
                  value={formData.user_id}
                  onChange={(e) => updateField("user_id", e.target.value)}
                  placeholder="Enter a unique identifier"
                />
                <p className="text-xs text-muted-foreground">
                  This is auto-generated but you can customize it
                </p>
              </div>

              <div className="rounded-lg border border-border bg-muted/50 p-4">
                <div className="flex items-start gap-3">
                  <Shield className="h-5 w-5 text-primary mt-0.5" />
                  <div>
                    <p className="font-medium text-foreground">Your data is private</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      We never share your financial information with third parties.
                      All analysis happens locally.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-6">
              {/* Monthly Income */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <Label>Monthly Income</Label>
                  <span className="text-sm font-medium font-mono">
                    ${formData.monthly_income.toLocaleString()}
                  </span>
                </div>
                <Slider
                  value={[formData.monthly_income]}
                  onValueChange={([value]) => updateField("monthly_income", value)}
                  min={2000}
                  max={15000}
                  step={100}
                />
                <p className="text-xs text-muted-foreground">
                  Your gross monthly income before taxes
                </p>
              </div>

              {/* Monthly Expenses */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <Label>Monthly Expenses</Label>
                  <span className="text-sm font-medium font-mono">
                    ${formData.monthly_expenses.toLocaleString()}
                  </span>
                </div>
                <Slider
                  value={[formData.monthly_expenses]}
                  onValueChange={([value]) => updateField("monthly_expenses", value)}
                  min={1000}
                  max={10000}
                  step={100}
                />
                <p className="text-xs text-muted-foreground">
                  Rent, food, utilities, subscriptions, etc.
                </p>
              </div>

              {/* Credit Score */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <Label>Credit Score</Label>
                  <span
                    className={`text-sm font-medium font-mono ${
                      formData.credit_score >= 740
                        ? "text-success"
                        : formData.credit_score >= 670
                          ? "text-warning"
                          : "text-destructive"
                    }`}
                  >
                    {formData.credit_score}
                  </span>
                </div>
                <Slider
                  value={[formData.credit_score]}
                  onValueChange={([value]) => updateField("credit_score", value)}
                  min={300}
                  max={850}
                  step={10}
                />
                <p className="text-xs text-muted-foreground">
                  Find this on Credit Karma or similar services
                </p>
              </div>

              {/* Current Debt */}
              <div className="flex flex-col gap-2">
                <Label htmlFor="debt">Current Debt</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="debt"
                    type="number"
                    value={formData.current_debt}
                    onChange={(e) => updateField("current_debt", Number(e.target.value))}
                    className="pl-7 font-mono"
                    min={0}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Credit cards, loans, etc.
                </p>
              </div>

              {/* Savings */}
              <div className="flex flex-col gap-2">
                <Label htmlFor="savings">Savings</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="savings"
                    type="number"
                    value={formData.savings}
                    onChange={(e) => updateField("savings", Number(e.target.value))}
                    className="pl-7 font-mono"
                    min={0}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Emergency fund and savings accounts
                </p>
              </div>

              {/* Live Preview */}
              <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Disposable Income</span>
                  <span
                    className={`text-lg font-bold font-mono ${
                      disposableIncome > 0 ? "text-success" : "text-destructive"
                    }`}
                  >
                    ${disposableIncome.toLocaleString()}/mo
                  </span>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col gap-6">
              {/* Risk Tolerance */}
              <div className="flex flex-col gap-3">
                <Label>Risk Tolerance</Label>
                <RadioGroup
                  value={formData.risk_tolerance}
                  onValueChange={(value) =>
                    updateField("risk_tolerance", value as "low" | "medium" | "high")
                  }
                  className="grid grid-cols-3 gap-4"
                >
                  {(["low", "medium", "high"] as const).map((level) => (
                    <label
                      key={level}
                      className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border p-4 transition-colors ${
                        formData.risk_tolerance === level
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-muted/50"
                      }`}
                    >
                      <RadioGroupItem value={level} className="sr-only" />
                      <span
                        className={`h-3 w-3 rounded-full ${
                          level === "low"
                            ? "bg-success"
                            : level === "medium"
                              ? "bg-warning"
                              : "bg-destructive"
                        }`}
                      />
                      <span className="text-sm font-medium capitalize">{level}</span>
                    </label>
                  ))}
                </RadioGroup>
                <p className="text-xs text-muted-foreground">
                  How comfortable are you stretching your budget?
                </p>
              </div>

              {/* Preferred Categories */}
              <div className="flex flex-col gap-3">
                <Label>Preferred Categories</Label>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {PRODUCT_CATEGORIES.map((category) => (
                    <label
                      key={category}
                      className={`flex cursor-pointer items-center gap-2 rounded-lg border p-3 text-sm transition-colors ${
                        formData.preferred_categories.includes(category)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-muted/50"
                      }`}
                    >
                      <Checkbox
                        checked={formData.preferred_categories.includes(category)}
                        onCheckedChange={() => toggleCategory(category)}
                      />
                      <span className="truncate">{category}</span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Select categories you shop most often
                </p>
              </div>

              {/* Profile Summary */}
              <div className="rounded-lg border border-border bg-muted/50 p-4">
                <p className="text-sm font-medium text-foreground mb-3">
                  Profile Summary
                </p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Income:</span>{" "}
                    <span className="font-medium font-mono">
                      ${formData.monthly_income.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Credit:</span>{" "}
                    <span className="font-medium font-mono">{formData.credit_score}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Disposable:</span>{" "}
                    <span className="font-medium font-mono text-success">
                      ${disposableIncome.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Risk:</span>{" "}
                    <span className="font-medium capitalize">{formData.risk_tolerance}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <div>
          {step > 1 ? (
            <Button variant="ghost" onClick={handleBack} className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          ) : (
            <Button variant="ghost" onClick={handleSkip}>
              Skip for Now
            </Button>
          )}
        </div>
        <Button onClick={handleNext} className="gap-2">
          {step === 3 ? (
            <>
              Save & Continue
              <Check className="h-4 w-4" />
            </>
          ) : (
            <>
              Next
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
