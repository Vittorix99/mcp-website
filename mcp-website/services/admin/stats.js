import { safeFetch } from "@/lib/fetch";
import { endpoints } from "@/config/endpoints";

export async function getAdminStats() {
  return safeFetch(endpoints.admin.getGeneralStats, "GET");
}