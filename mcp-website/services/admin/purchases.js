// services/admin/purchases.js

import { safeFetch } from "@/lib/fetch";
import { endpoints } from "@/config/endpoints";

export async function getAllPurchases() {
  return safeFetch(endpoints.admin.getAllPurchases, "GET");
}

export async function getPurchase() {
  return safeFetch(endpoints.admin.getPurchase, "GET");
}
export async function getPurchaseById(purchase_id) {
  const url = `${endpoints.admin.getPurchase}?id=${purchase_id}`;
  return safeFetch(url, "GET");
}

export async function createPurchase(data) {
  return safeFetch(endpoints.admin.createPurchase, "POST", data);
}

export async function deletePurchase(purchase_id) {
  return safeFetch(endpoints.admin.deletePurchase, "DELETE", { purchase_id });
}