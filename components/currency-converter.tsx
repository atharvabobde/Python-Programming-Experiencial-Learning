"use client"

import { useState } from "react"
import type { FormEvent } from "react"

const CURRENCIES = [
  "USD", "INR", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SGD", "NZD",
  "AED", "SAR", "ZAR", "BDT", "PKR", "NPR", "LKR", "THB", "MYR", "KRW",
]

type Conversion = {
  id: string
  date: Date
  amount: number
  source: string
  target: string
  rate: number
  result: number
  updated: string
}

function formatNumber(value: number, maximumFractionDigits = 2) {
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits,
  }).format(value)
}

function escapeCsv(value: string | number) {
  return `"${String(value).replaceAll('"', '""')}"`
}

export default function CurrencyConverter() {
  const [amount, setAmount] = useState("100")
  const [source, setSource] = useState("USD")
  const [target, setTarget] = useState("INR")
  const [latest, setLatest] = useState<Conversion | null>(null)
  const [history, setHistory] = useState<Conversion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState("")
  const [hasError, setHasError] = useState(false)

  async function handleConvert(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const numericAmount = Number(amount)

    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setHasError(true)
      setStatus("Enter an amount greater than zero.")
      return
    }

    setIsLoading(true)
    setHasError(false)
    setStatus("Getting the latest available rate…")

    try {
      const response = await fetch(`/api/rates/${encodeURIComponent(source)}`, { cache: "no-store" })
      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.error ?? "Exchange rates could not be retrieved.")
      }

      const rate = payload.rates?.[target]
      if (typeof rate !== "number" || !Number.isFinite(rate)) {
        throw new Error(`The rate for ${target} is not available right now.`)
      }

      const conversion: Conversion = {
        id: crypto.randomUUID(),
        date: new Date(),
        amount: numericAmount,
        source,
        target,
        rate,
        result: numericAmount * rate,
        updated: payload.updated ?? "Not provided",
      }

      setLatest(conversion)
      setHistory((previous) => [conversion, ...previous].slice(0, 100))
      setStatus("Conversion complete. Rates are indicative and may be delayed.")
      setHasError(false)
    } catch (error) {
      setHasError(true)
      setStatus(error instanceof Error ? error.message : "Something went wrong. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  function swapCurrencies() {
    setSource(target)
    setTarget(source)
    setLatest(null)
  }

  function exportCsv() {
    const rows = [
      ["Date & Time", "Amount", "From Currency", "To Currency", "Exchange Rate", "Converted Amount"],
      ...history.map((entry) => [
        entry.date.toLocaleString(),
        formatNumber(entry.amount),
        entry.source,
        entry.target,
        entry.rate.toFixed(6),
        formatNumber(entry.result),
      ]),
    ]
    const csv = `\uFEFF${rows.map((row) => row.map(escapeCsv).join(",")).join("\r\n")}`
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }))
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = "conversion_history.csv"
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1_000)
  }

  return (
    <div className="site-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">FX/</span>
          <span>Currency Converter</span>
        </div>
        <div className="market-note"><span className="live-dot" aria-hidden="true" /> Live rates, no account needed</div>
      </header>

      <main>
        <section className="intro" aria-labelledby="page-title">
          <p className="eyebrow">A smarter way to convert</p>
          <h1 id="page-title">Know what your money is worth.</h1>
          <p className="intro-copy">
            Quick, clear currency conversions with the latest available exchange rates. Your history stays in this page and is never sent to an account.
          </p>
        </section>

        <section className="main-grid" aria-label="Currency conversion">
          <div className="panel converter-panel">
            <div className="panel-heading">
              <div>
                <h2 className="panel-title">Make a conversion</h2>
                <p className="panel-description">Choose an amount and currency pair.</p>
              </div>
              <span className="fresh-badge"><span className="live-dot" aria-hidden="true" /> 21 currencies</span>
            </div>

            <form onSubmit={handleConvert}>
              <label className="field-label" htmlFor="amount">Amount</label>
              <input
                className="amount-input"
                id="amount"
                name="amount"
                type="number"
                min="0.01"
                step="any"
                inputMode="decimal"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                required
                aria-describedby="conversion-status"
              />

              <div className="currency-row">
                <div>
                  <label className="field-label" htmlFor="source">From</label>
                  <select className="currency-select" id="source" value={source} onChange={(event) => setSource(event.target.value)}>
                    {CURRENCIES.map((currency) => <option key={currency} value={currency}>{currency}</option>)}
                  </select>
                </div>
                <button className="swap-button" type="button" onClick={swapCurrencies} aria-label="Swap currencies">⇄</button>
                <div>
                  <label className="field-label" htmlFor="target">To</label>
                  <select className="currency-select" id="target" value={target} onChange={(event) => setTarget(event.target.value)}>
                    {CURRENCIES.map((currency) => <option key={currency} value={currency}>{currency}</option>)}
                  </select>
                </div>
              </div>

              <button className="convert-button" type="submit" disabled={isLoading}>
                {isLoading ? "FETCHING RATE" : "CONVERT CURRENCY"}
                <span className="arrow-icon" aria-hidden="true">↗</span>
              </button>
            </form>
            <p id="conversion-status" className="status-message" data-error={hasError} role={hasError ? "alert" : "status"} aria-live="polite">
              {status || "Rates are retrieved when you convert."}
            </p>
          </div>

          <aside className="panel result-panel" aria-live="polite" aria-label="Conversion result">
            <p className="result-kicker">Your conversion</p>
            <div className="result-content">
              {latest ? (
                <>
                  <p className="result-source">{formatNumber(latest.amount)} {latest.source} equals</p>
                  <strong className="result-value">{formatNumber(latest.result)}</strong>
                  <p className="result-target">{latest.target}</p>
                </>
              ) : (
                <p className="result-placeholder">Your converted amount will appear here.</p>
              )}
            </div>
            <div className="rate-line">
              <div className="rate-row"><span>Exchange rate</span><strong>{latest ? `1 ${latest.source} = ${formatNumber(latest.rate, 6)} ${latest.target}` : "—"}</strong></div>
              <div className="rate-row"><span>Rates updated</span><strong>{latest?.updated ?? "After conversion"}</strong></div>
            </div>
          </aside>
        </section>

        <section className="panel history-section" aria-labelledby="history-title">
          <div className="history-heading">
            <div>
              <h2 className="history-title" id="history-title">Recent conversions</h2>
              <p className="history-subtitle">Up to 100 entries for this page session only.</p>
            </div>
            <div className="history-actions">
              <button className="ghost-button" type="button" onClick={exportCsv} disabled={history.length === 0}>Download CSV</button>
              <button className="ghost-button" type="button" onClick={() => setHistory([])} disabled={history.length === 0}>Clear</button>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th scope="col">Time</th><th scope="col">Amount</th><th scope="col">From</th><th scope="col">To</th><th scope="col">Rate</th><th scope="col">Converted</th></tr>
              </thead>
              <tbody>
                {history.length > 0 ? history.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.date.toLocaleString()}</td>
                    <td>{formatNumber(entry.amount)} {entry.source}</td>
                    <td>{entry.source}</td>
                    <td>{entry.target}</td>
                    <td>{formatNumber(entry.rate, 6)}</td>
                    <td>{formatNumber(entry.result)} {entry.target}</td>
                  </tr>
                )) : (
                  <tr><td className="empty-history" colSpan={6}>Your conversions will show here during this page session.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span><strong>Rate provider:</strong> open.er-api.com</span>
        <span>Rates are indicative and may be delayed. Not financial advice.</span>
      </footer>
    </div>
  )
}
