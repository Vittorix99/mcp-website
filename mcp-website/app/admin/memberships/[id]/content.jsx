"use client";

// Force SSR in Next.js (important for Firebase Hosting)

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Loader2, Wallet } from "lucide-react";
import { motion } from "framer-motion";
import { routes } from "@/config/routes"

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import {
  Table, TableHeader, TableBody, TableRow,
  TableHead, TableCell
} from "@/components/ui/table";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";

import { useAdminMemberships } from "@/hooks/useAdminMemberships";
import { EventThumbnail } from "@/components/admin/events/EventThumbnail";
import { AdminLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome";

export default function MembershipContent({ id }) {
  const router = useRouter();

  const {
    selected: member,
    loading,
    loadOne,
    extrasLoading,
    createWalletPass,
  } = useAdminMemberships({ autoLoadList: false });

  const handleCreateWallet = async () => {
    if (!id) return;
    await createWalletPass(id);
  };

  const [purchaseFilter, setPurchaseFilter] = useState("");
  const [purchaseSortDesc, setPurchaseSortDesc] = useState(true);
  const loadedMembershipRef = useRef(null);

  useEffect(() => {
    if (!id) return;
    if (loadedMembershipRef.current === id) return;
    loadedMembershipRef.current = id;
    loadOne(id);
  }, [id, loadOne]);

  const formatDate = (iso) => {
    if (!iso) return "-";
    const date = new Date(iso);
    return date.toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    });
  };

  const filteredPurchases = useMemo(() => {
    if (!member || !member.purchases) return [];
    let arr = [...member.purchases];
    if (purchaseFilter) {
      arr = arr.filter(p => p.type === purchaseFilter);
    }
    arr.sort((a, b) =>
      purchaseSortDesc
        ? new Date(b.timestamp) - new Date(a.timestamp)
        : new Date(a.timestamp) - new Date(b.timestamp)
    );
    return arr;
  }, [member, purchaseFilter, purchaseSortDesc]);

  // Mostra uno spinner finché i dettagli base non sono pronti
  if (loading || !member) {
    return <AdminLoading label="Caricamento membro..." />;
  }

  const {
    id: membershipId,
    name, surname, email, phone, birthdate,
    start_date, end_date, subscription_valid,
    membership_sent, wallet_url, wallet_pass_id, purchase_id,
    events = []
  } = member;

  return (
    <TooltipProvider>
      <div className="text-gray-50 min-h-screen p-6 lg:p-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="max-w-5xl mx-auto space-y-6">
          <AdminPageHeader
            title={`${name} ${surname}`}
            description={email}
            backHref={routes.admin.memberships}
            backLabel="Torna ai membri"
          />

          {/* Dettagli membro */}
          <Card className="bg-zinc-900 border border-zinc-700 shadow-lg">
            <CardHeader><CardTitle>Dettagli Membro</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-base">
              <div><strong>ID:</strong> {membershipId || "-"}</div>
              <div><strong>Email:</strong> {email}</div>
              <div><strong>Telefono:</strong> {phone || "-"}</div>
              <div><strong>Data di nascita:</strong> {birthdate || "-"}</div>
              <div><strong>Inizio sottoscrizione:</strong> {formatDate(start_date)}</div>
              <div>
                <strong>Validità tessera:</strong>{" "}
                <Badge variant={subscription_valid ? "success" : "destructive"} className="p-2">
                  {subscription_valid ? end_date : "Scaduta"}
                </Badge>
              </div>
              <div>
                <strong>Tessera inviata:</strong>{" "}
                <Badge variant={membership_sent ? "success" : "secondary"} className="p-2">
                  {membership_sent ? "Sì" : "No"}
                </Badge>
              </div>

              {wallet_url ? (
                <div className="flex items-center gap-2 col-span-full">
                  <Button
                    variant="link"
                    size="icon"
                    onClick={() => window.open(wallet_url, "_blank")}
                  >
                    <Wallet className="h-5 w-5" />
                  </Button>
                  <span>Apri Wallet</span>
                  {wallet_pass_id && (
                    <span className="text-xs text-gray-500">({wallet_pass_id})</span>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 col-span-full text-yellow-400">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span className="text-sm">Wallet pass non creato!</span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={loading}
                    onClick={handleCreateWallet}
                    className="ml-2"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Crea"}
                  </Button>
                </div>
              )}

                  {purchase_id && (
                <div className="col-span-full">
                  <Button
                    size="sm"
                    onClick={() => router.push(routes.admin.purchasesDetails(purchase_id))}
                  >
                    Vai all'acquisto
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Storico Rinnovi */}
          <Card className="bg-zinc-900 border border-zinc-700 shadow-lg">
            <CardHeader><CardTitle>Storico Rinnovi ({(member.renewals || []).length})</CardTitle></CardHeader>
            <CardContent>
              {(member.renewals || []).length ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Anno</TableHead>
                        <TableHead>Dal</TableHead>
                        <TableHead>Al</TableHead>
                        <TableHead>Quota</TableHead>
                        <TableHead>Acquisto</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {[...(member.renewals || [])].sort((a, b) => b.year - a.year).map((r) => (
                        <TableRow key={r.year}>
                          <TableCell><Badge variant="secondary">{r.year}</Badge></TableCell>
                          <TableCell>{formatDate(r.start_date)}</TableCell>
                          <TableCell>{r.end_date || "-"}</TableCell>
                          <TableCell>{r.fee != null ? `${r.fee} €` : "-"}</TableCell>
                          <TableCell>
                            {r.purchase_id ? (
                              <Button size="sm" variant="link" onClick={() => router.push(routes.admin.purchasesDetails(r.purchase_id))}>
                                Vai
                              </Button>
                            ) : "-"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-sm text-gray-400">Nessun rinnovo registrato.</p>
              )}
            </CardContent>
          </Card>

          {/* Acquisti */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center flex-wrap gap-3">
                <CardTitle>Acquisti ({filteredPurchases.length})</CardTitle>
                <div className="flex gap-2 items-center">
                  <select className="bg-zinc-900 border border-zinc-700 rounded px-3 py-1 text-sm"
                    value={purchaseFilter} onChange={e => setPurchaseFilter(e.target.value)}>
                    <option value="">Tutti</option>
                    <option value="membership">Membership</option>
                    <option value="event">Evento</option>
                    <option value="event_and_membership">Membership e Evento</option>
                  </select>
                  <Button variant="ghost" size="sm" onClick={() => setPurchaseSortDesc(p => !p)}>
                    Ordina {purchaseSortDesc ? "↓" : "↑"}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {extrasLoading ? (
                <div className="space-y-2">
                  <div className="h-6 w-40 bg-zinc-800 animate-pulse rounded" />
                  <div className="h-6 w-full bg-zinc-800 animate-pulse rounded" />
                  <div className="h-6 w-5/6 bg-zinc-800 animate-pulse rounded" />
                  <div className="h-6 w-4/6 bg-zinc-800 animate-pulse rounded" />
                </div>
              ) : filteredPurchases.length ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Importo</TableHead>
                        <TableHead>Data</TableHead>
                        <TableHead>Dettagli</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredPurchases.map(p => (
                        <TableRow key={p.ref_id || p.transaction_id}>
                          <TableCell>{p.type}</TableCell>
                          <TableCell>{p.amount_total} {p.currency}</TableCell>
                          <TableCell>{formatDate(p.timestamp)}</TableCell>
                          <TableCell>
                            {p.ref_id ? (
                              <Button
                                size="sm"
                                variant="link"
                                onClick={() => router.push(routes.admin.purchasesDetails(p.id))}
                              >
                                Vai
                              </Button>
                            ) : "-"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-sm text-gray-400">Nessun acquisto trovato.</p>
              )}
            </CardContent>
          </Card>

          {/* Eventi */}
          <Card>
            <CardHeader><CardTitle>Eventi Partecipati ({events.length})</CardTitle></CardHeader>
            <CardContent>
              {extrasLoading ? (
                <div className="space-y-2">
                  <div className="h-6 w-44 bg-zinc-800 animate-pulse rounded" />
                  <div className="h-6 w-full bg-zinc-800 animate-pulse rounded" />
                  <div className="h-6 w-5/6 bg-zinc-800 animate-pulse rounded" />
                </div>
              ) : events.length ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Thumbnail</TableHead>
                      <TableHead>Evento</TableHead>
                      <TableHead>Data</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {events.map(e => (
                      <TableRow key={e.id}>
                        <TableCell>
                          {e.image ? (
                            <EventThumbnail imageName={e.image} alt={e.title} />
                          ) : "-"}
                        </TableCell>
                        <TableCell>
                          <Button variant="link" onClick={() => router.push(routes.admin.eventDetails(e.id))}>
                            {e.title}
                          </Button>
                        </TableCell>
                        <TableCell>{e.date}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-sm text-gray-400">Nessun evento partecipato.</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </TooltipProvider>
  );
}
