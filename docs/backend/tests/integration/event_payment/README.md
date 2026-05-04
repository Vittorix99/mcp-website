# Event Payments Integration (PayPal Sandbox)

This suite hits real PayPal Sandbox APIs. To run the **approved capture** flow you must manually approve a PayPal order and provide its ID.

## 1) Prerequisites
- `PAYPAL_ENV=sandbox`
- `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` set in `.env.integration`
- A **future** event with `status=active` exists in Firestore
- `FUNCTIONS_BASE_URL` points to your local functions URL

## 2) Create a PayPal order (create_order_event)
Call the public endpoint:
```
POST {FUNCTIONS_BASE_URL}/create_order_event
```

Example body:
```json
{
  "cart": [
    {
      "eventId": "EVENT_ID",
      "participants": [
        {
          "name": "Mario",
          "surname": "Rossi",
          "email": "mcpweb.testing+paypal_test@gmail.com",
          "phone": "+390000000000",
          "birthdate": "01-01-1990"
        }
      ]
    }
  ]
}
```

In the response, locate the `approve` link from `links[]` and the `id` (order id).

## 3) Approve the order
Open the `approve` link in an **incognito** browser window and log in with a PayPal **sandbox buyer** account.
Complete the approval.

## 4) Set the approved order id
Add to `.env.integration`:
```
PAYPAL_APPROVED_ORDER_ID=ORDER_ID_FROM_STEP_2
```

## 5) Run the approved capture test
```
pytest -m integration tests/integration/event_payment -k approved
```

Notes:
- The integration tests will create real PayPal sandbox orders.
- If the approved order id expires, repeat the flow to get a new one.
