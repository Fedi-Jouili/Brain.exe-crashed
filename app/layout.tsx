import type { Metadata, Viewport } from "next"
import { Inter, Fira_Code } from "next/font/google"
import "./globals.css"

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-sans",
})

const firaCode = Fira_Code({ 
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: "FinCommerce Engine | Smart Shopping with Financial Intelligence",
  description: "AI-powered product recommendations based on your real financial situation. Make informed purchase decisions with personalized affordability analysis.",
}

export const viewport: Viewport = {
  themeColor: "#4A90E2",
  width: "device-width",
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${firaCode.variable} font-sans`}>
        {children}
      </body>
    </html>
  )
}
