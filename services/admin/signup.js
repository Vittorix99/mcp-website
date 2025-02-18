import { endpoints } from '@/config/endpoints';
import { getAdminToken } from '@/config/firebase';

/**
 * Client-side service functions for signup functionality
 */

// Public signup request
export async function createSignupRequest(data) {
  try {
    const response = await fetch(endpoints.signupRequest, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create signup request');
    }

    return response.json();
  } catch (error) {
    console.error('Error creating signup request:', error);
    throw error;
  }
}

// Admin functions
export async function getSignupRequests(requestId = null) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const url = requestId 
      ? `${endpoints.admin.getSignupRequests}?id=${requestId}`
      : endpoints.admin.getSignupRequests;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch signup requests');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching signup requests:', error);
    throw error;
  }
}

export async function updateSignupRequest(requestId, data) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.updateSignupRequest, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ id: requestId, ...data }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update signup request');
    }

    return response.json();
  } catch (error) {
    console.error('Error updating signup request:', error);
    throw error;
  }
}

export async function deleteSignupRequest(requestId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${endpoints.admin.deleteSignupRequest}?id=${requestId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete signup request');
    }

    return response.json();
  } catch (error) {
    console.error('Error deleting signup request:', error);
    throw error;
  }
}

export async function acceptSignupRequest(requestId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.acceptSignupRequest, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ id: requestId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to accept signup request');
    }

    return response.json();
  } catch (error) {
    console.error('Error accepting signup request:', error);
    throw error;
  }
}