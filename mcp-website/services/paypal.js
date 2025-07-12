import { endpoints } from "../config/endpoints";

/**
 * Crea un ordine PayPal sul backend.
 * @param {Object} cart - Oggetto con le info di acquisto (sarà messo in un array).
 * @param {string} purchase_type - Uno tra "event", "membership", "event_and_membership".
 * @returns {Promise<Object>} - Dati dell’ordine o errore.
 */
export async function createOrder(payload) {
  try {
    const response = await fetch(endpoints.createOrder, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        cart: [payload.cart], // anche se è uno solo, sempre array
        purchase_type: payload.purchase_type,
      }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Errore durante la creazione dell’ordine:", error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Cattura un ordine PayPal confermato dal client.
 * @param {string} order_id - ID dell’ordine da catturare.
 * @returns {Promise<Object>} - Dati del purchase registrato.
 */
export async function onApprove(order_id) {
  try {
    const response = await fetch(endpoints.captureOrder, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ order_id }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Errore durante la cattura dell’ordine:", error.message);
    return { success: false, error: error.message };
  }
}