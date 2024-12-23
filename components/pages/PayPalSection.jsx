import { initialOptions } from "@/paypal"; // Assicurati che `initialOptions` sia configurato correttamente
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { useState } from "react";

export default function PayPalSection({ event }) {
    const [message, setMessage] = useState("");

    const createOrder = async () => {
        try {
            const response = await fetch("/api/orders", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    eventId: event.id, // ID dell'evento passato come prop
                    ticketPrice: event.price, // Prezzo del biglietto passato come prop
                }),
            });

            const orderData = await response.json();

            if (orderData.id) {
                return orderData.id;
            } else {
                const errorDetail = orderData?.details?.[0];
                const errorMessage = errorDetail
                    ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`
                    : JSON.stringify(orderData);

                throw new Error(errorMessage);
            }
        } catch (error) {
            console.error(error);
            setMessage(`Could not initiate PayPal Checkout: ${error.message}`);
        }
    };

    const onApprove = async (data, actions) => {
        try {
            const response = await fetch(`/api/orders/${data.orderID}/capture`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            const orderData = await response.json();

            if (orderData.status === "COMPLETED") {
                setMessage(
                    "Payment successful! Your ticket has been generated and sent to your email."
                );
                console.log(
                    "Order details:",
                    JSON.stringify(orderData, null, 2)
                );
            } else {
                throw new Error("Transaction could not be completed.");
            }
        } catch (error) {
            console.error(error);
            setMessage(`Transaction failed: ${error.message}`);
        }
    };

    return (
        <div className="container mx-auto px-4">
            <h2 className="text-xl font-bold text-center mb-4">
                Purchase Ticket for {event.title}
            </h2>
            <p className="text-center mb-4">
                Price: ${event.price}
            </p>
            <PayPalScriptProvider options={initialOptions}>
                <PayPalButtons
                    style={{
                        shape: "pill",
                        layout: "vertical",
                        color: "blue",
                        label: "paypal",
                    }}
                    createOrder={createOrder}
                    onApprove={onApprove}
                />
            </PayPalScriptProvider>
            {message && (
                <p className="text-center mt-4 text-red-500">{message}</p>
            )}
        </div>
    );
}