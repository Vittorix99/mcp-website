export async function sendContactRequest({ name, email, message, sendCopy = false }) {
    try {
      const response = await fetch('/api/contact', {
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
      });
  
      const result = await response.json();
  
      if (!result.success) {
        throw new Error(result.error || 'Failed to send the message');
      }
  
      return result.message; // Return the success message
    } catch (error) {
      console.error('Service Error:', error.message);
      throw error; // Re-throw for the caller to handle
    }
  }