import { NextResponse } from "next/server"

const CURRENCIES = new Set([
  "USD", "INR", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SGD", "NZD",
  "AED", "SAR", "ZAR", "BDT", "PKR", "NPR", "LKR", "THB", "MYR", "KRW",
])

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ base: string }> },
) {
  const { base: rawBase } = await params
  const base = rawBase.toUpperCase()

  if (!CURRENCIES.has(base)) {
    return NextResponse.json({ error: "Unsupported base currency." }, { status: 400 })
  }

  try {
    const upstream = await fetch(`https://open.er-api.com/v6/latest/${base}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
      headers: { Accept: "application/json" },
    })

    if (!upstream.ok) {
      return NextResponse.json({ error: "The exchange-rate service is unavailable." }, { status: 502 })
    }

    const data = await upstream.json()
    const rates = data?.rates ?? data?.conversion_rates

    if (data?.result !== "success" || !rates || typeof rates !== "object") {
      return NextResponse.json({ error: "Exchange rates could not be retrieved." }, { status: 502 })
    }

    return NextResponse.json({
      base,
      rates,
      updated: data.time_last_update_utc ?? "Not provided",
    }, {
      headers: { "Cache-Control": "no-store" },
    })
  } catch {
    return NextResponse.json({ error: "Could not connect to the exchange-rate service. Try again shortly." }, { status: 502 })
  }
}
