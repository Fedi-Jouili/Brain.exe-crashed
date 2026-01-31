"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  AlertCircle,
  RefreshCcw,
  WifiOff,
  Lock,
  ServerCrash,
  Clock,
} from "lucide-react"
import { cn } from "@/lib/utils"

type ErrorType = "network" | "auth" | "server" | "timeout" | "generic"

interface ErrorStateProps {
  type?: ErrorType
  title?: string
  message?: string
  onRetry?: () => void
  onAction?: () => void
  actionLabel?: string
  className?: string
}

const errorConfig: Record<
  ErrorType,
  { icon: typeof AlertCircle; title: string; message: string }
> = {
  network: {
    icon: WifiOff,
    title: "Connection Error",
    message:
      "Unable to connect to the server. Please check your internet connection and try again.",
  },
  auth: {
    icon: Lock,
    title: "Authentication Required",
    message: "Your session has expired. Please log in again to continue.",
  },
  server: {
    icon: ServerCrash,
    title: "Server Error",
    message:
      "Something went wrong on our end. Our team has been notified and is working on a fix.",
  },
  timeout: {
    icon: Clock,
    title: "Request Timed Out",
    message:
      "The request took too long to complete. Please try again in a moment.",
  },
  generic: {
    icon: AlertCircle,
    title: "Something Went Wrong",
    message: "An unexpected error occurred. Please try again.",
  },
}

export function ErrorState({
  type = "generic",
  title,
  message,
  onRetry,
  onAction,
  actionLabel,
  className,
}: ErrorStateProps) {
  const config = errorConfig[type]
  const Icon = config.icon

  return (
    <Card className={cn("border-destructive/50 bg-destructive/5", className)}>
      <CardContent className="flex flex-col items-center text-center p-8">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10 mb-4">
          <Icon className="h-7 w-7 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">
          {title || config.title}
        </h3>
        <p className="text-sm text-muted-foreground max-w-sm mb-6">
          {message || config.message}
        </p>
        <div className="flex gap-3">
          {onRetry && (
            <Button variant="outline" onClick={onRetry} className="gap-2">
              <RefreshCcw className="h-4 w-4" />
              Try Again
            </Button>
          )}
          {onAction && actionLabel && (
            <Button onClick={onAction}>{actionLabel}</Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Inline error message for forms
interface InlineErrorProps {
  message: string
  className?: string
}

export function InlineError({ message, className }: InlineErrorProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive",
        className
      )}
    >
      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  )
}

// Full page error state
interface FullPageErrorProps {
  type?: ErrorType
  title?: string
  message?: string
  onRetry?: () => void
}

export function FullPageError({
  type = "generic",
  title,
  message,
  onRetry,
}: FullPageErrorProps) {
  const config = errorConfig[type]
  const Icon = config.icon

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10 mb-6">
        <Icon className="h-10 w-10 text-destructive" />
      </div>
      <h2 className="text-2xl font-bold text-foreground mb-2">
        {title || config.title}
      </h2>
      <p className="text-muted-foreground max-w-md mb-8">
        {message || config.message}
      </p>
      {onRetry && (
        <Button onClick={onRetry} className="gap-2">
          <RefreshCcw className="h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  )
}
