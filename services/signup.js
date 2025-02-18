import { endpoints } from '../config/endpoints';

export async function submitSignupRequest(formData) {
  try {
    const response = await fetch(endpoints.signupRequest, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    });

    let data = await response.json();

    // If the data is a JSON string, convert it to an object
    if (typeof data === 'string') {
      data = JSON.parse(data);
    }

    if (!response.ok) {
      if (response.status === 409){
        return {success: false, error: "This email is already registered."};
      }
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }

    return { success: true, data };
  } catch (error) {
    

    return { success: false, error: error.message };
  }
}