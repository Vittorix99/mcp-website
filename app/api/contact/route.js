export async function POST(req) {
  try {
    // Extract the body data
    const { name, email, message, send_copy: sendCopy } = await req.json();

    // Make a POST request to the Firebase Cloud Function
    const firebaseResponse = await fetch(
      'https://contact-us2-cgp4ofmn2q-uc.a.run.app',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          message,
          send_copy: sendCopy,
        }),
      }
    );

    if (!firebaseResponse.ok) {
      const errorText = await firebaseResponse.text();
      throw new Error(`Firebase Server Error: ${errorText}`);
    }

    const data = await firebaseResponse.text(); // Adjust if Firebase sends JSON

    // Return success response
    return Response.json({ success: true, message: data }, { status: 200 });
  } catch (error) {
    console.error('API Error:', error.message);

    // Return error response
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}