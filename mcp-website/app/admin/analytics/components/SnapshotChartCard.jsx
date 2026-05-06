"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const TITLE_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif'
const BODY_FONT = 'Charter, Georgia, "Times New Roman", serif'

export default function SnapshotChartCard({ title, loading, error, empty, children }) {
  return (
    <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm uppercase tracking-[0.08em]" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[320px] overflow-hidden px-3 pb-3 pt-0 sm:h-[280px] sm:px-6 sm:pb-6">
        {loading ? (
          <div className="h-full animate-pulse border border-[var(--color-border)] bg-[var(--color-black)]" />
        ) : error ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--color-red)]" style={{ fontFamily: BODY_FONT }}>
            {error}
          </div>
        ) : empty ? (
          <div className="flex h-full items-center justify-center text-sm text-[var(--color-off)]" style={{ fontFamily: BODY_FONT }}>
            Nessun dato disponibile
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  )
}
