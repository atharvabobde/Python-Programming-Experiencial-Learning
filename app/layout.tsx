import type { Metadata, Viewport } from "next"
import type { ReactNode } from "react"
import "./globals.css"

export const metadata: Metadata = {
  title: "Currency Converter — Clear, Current Exchange Rates",
  description:
    "Convert between 21 global currencies with current exchange rates, a private on-page history, and an Excel-friendly CSV export.",
  applicationName: "Currency Converter",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f5f7f2",
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
