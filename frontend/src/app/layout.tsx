import type React from "react"
import type { Metadata } from "next"
import { Be_Vietnam_Pro } from "next/font/google"
// Analytics removed as it's extra and not part of core requirements
import { Suspense } from "react"
import { Toaster } from "sonner"
import "./globals.css"

const beVietnamPro = Be_Vietnam_Pro({
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
  display: "swap",
  variable: "--font-be-vietnam-pro",
})

export const metadata: Metadata = {
  title: "Get More Diners - Find & Connect with Potential Restaurant Customers",
  description:
    "Get More Diners helps restaurant owners search for potential customers nearby and send them personalized offers via email and SMS to grow their business.",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
      </head>
      <body className={`font-sans ${beVietnamPro.variable}`}>
        <Suspense fallback={null}>{children}</Suspense>
        <Toaster />
      </body>
    </html>
  )
}