import {endpoints} from '../config/endpoints';



export async function createOrder(cart){


try {
    const response = await fetch(endpoints.createOrder, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            cart: [
                    cart
                ]
        }),
    });

  
    let data = await response.json();

    // Se il dato è una stringa JSON, convertilo in oggetto
    if (typeof data === 'string') {
        data = JSON.parse(data);
    }

    
    return data;

} catch (error) {
    console.error('Error while creating order:', error.message);
    return { success: false, error: error.message };
    }
}


export async function onApprove(order_id) {

    try {

        const response = await fetch(endpoints.captureOrder , {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                order_id: order_id,
            
            }), 
        })

        const orderData = await response.json()
        return orderData;

    } catch (error) {
        console.error('Error while capturing order:', error.message);
        return { success: false, error: error.message };
    }

  
}

