"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { routes } from "@/config/routes"
import SubscribersTab from "@/components/admin/sender/SubscribersTab"
import SubscriberDrawer from "@/components/admin/sender/SubscriberDrawer"
import GroupsTab from "@/components/admin/sender/GroupsTab"
import SegmentsTab from "@/components/admin/sender/SegmentsTab"
import FieldsTab from "@/components/admin/sender/FieldsTab"

export default function SenderCRMPage() {
  const router = useRouter()
  const [selectedSubscriber, setSelectedSubscriber] = useState(null)
  const [subscriberReloadKey, setSubscriberReloadKey] = useState(0)

  function handleGroupChanged() {
    setSubscriberReloadKey((k) => k + 1)
  }

  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div>
        <Button variant="ghost" onClick={() => router.push(routes.admin.sender.campaigns)} className="mb-1 -ml-2">
          <ArrowLeft className="mr-2 h-4 w-4" /> Campagne
        </Button>
        <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">CRM — Sender</h1>
        <p className="text-gray-300">Gestisci subscriber, gruppi, segmenti e campi.</p>
      </div>

      <Tabs defaultValue="subscribers">
        <TabsList className="bg-zinc-900 border border-zinc-700">
          <TabsTrigger value="subscribers">Subscriber</TabsTrigger>
          <TabsTrigger value="groups">Gruppi</TabsTrigger>
          <TabsTrigger value="segments">Segmenti</TabsTrigger>
          <TabsTrigger value="fields">Campi</TabsTrigger>
        </TabsList>

        <TabsContent value="subscribers" className="mt-6">
          <div className={`grid gap-6 ${selectedSubscriber ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1"}`}>
            <SubscribersTab
              onSelectSubscriber={setSelectedSubscriber}
              reloadKey={subscriberReloadKey}
            />
            {selectedSubscriber && (
              <div className="lg:sticky lg:top-4 lg:self-start">
                <SubscriberDrawer
                  subscriber={selectedSubscriber}
                  onClose={() => setSelectedSubscriber(null)}
                  onDeleted={() => { setSelectedSubscriber(null); handleGroupChanged() }}
                  onUpdated={(updated) => setSelectedSubscriber(updated)}
                  onGroupChanged={handleGroupChanged}
                />
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="groups" className="mt-6">
          <GroupsTab />
        </TabsContent>

        <TabsContent value="segments" className="mt-6">
          <SegmentsTab />
        </TabsContent>

        <TabsContent value="fields" className="mt-6">
          <FieldsTab />
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
