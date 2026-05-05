"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { routes } from "@/config/routes"
import SubscribersTab from "@/components/admin/sender/SubscribersTab"
import SubscriberDrawer from "@/components/admin/sender/SubscriberDrawer"
import GroupsTab from "@/components/admin/sender/GroupsTab"
import SegmentsTab from "@/components/admin/sender/SegmentsTab"
import FieldsTab from "@/components/admin/sender/FieldsTab"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function SenderCRMPage() {
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
      <AdminPageHeader
        title="CRM Sender"
        description="Gestisci subscriber, gruppi, segmenti e campi."
        backHref={routes.admin.sender.campaigns}
        backLabel="Torna alle campagne"
      />

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
