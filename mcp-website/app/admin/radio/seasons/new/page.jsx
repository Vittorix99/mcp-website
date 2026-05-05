import { SeasonForm } from "@/components/admin/radio/SeasonForm"
import { routes } from "@/config/routes"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function NewSeasonPage() {
  return (
    <div>
      <AdminPageHeader title="Nuova stagione" backHref={routes.admin.radio.index} backLabel="Torna alla radio" />

      <SeasonForm mode="create" />
    </div>
  )
}
