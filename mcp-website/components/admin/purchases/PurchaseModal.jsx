import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

export function PurchaseModal({ purchase, onClose }) {
  if (!purchase) return null

  const rows = [
    ["Transaction ID", purchase.transaction_id],
    ["Order ID", purchase.order_id],
    ["Payer Name", `${purchase.payer_name} ${purchase.payer_surname}`],
    ["Email", purchase.payer_email],
    ["Type", purchase.type],
    ["Payment Method", purchase.payment_method],
    ["Ref ID", purchase.ref_id],
    ["Status", purchase.status],
    ["Currency", purchase.currency],
    ["Amount Total", `${parseFloat(purchase.amount_total).toFixed(2)} €`],
    ["Paypal Fee", `${parseFloat(purchase.paypal_fee).toFixed(2)} €`],
    ["Net Amount", `${parseFloat(purchase.net_amount).toFixed(2)} €`],
    ["Timestamp", new Date(purchase.timestamp).toLocaleString("it-IT")],
  ]

  return (
    <Dialog open={!!purchase} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 text-white border-zinc-700 max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-xl">Dettagli Acquisto</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          {rows.map(([label, value]) => (
            <div key={label} className="flex justify-between border-b border-zinc-700 py-1">
              <span className="text-muted-foreground">{label}</span>
              <span className="text-right max-w-[60%] truncate">{value || "-"}</span>
            </div>
          ))}
        </div>
        <div className="pt-4 flex justify-end">
          <Button onClick={onClose}>Chiudi</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}