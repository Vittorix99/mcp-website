import { endpoints } from '@/config/endpoints';
import { getAdminToken } from '@/config/firebase';

// ... (keep existing public functions)

// Admin functions
export async function getNewsletterSignups(signupId = null) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const url = signupId 
      ? `${endpoints.admin.newsletter.getAll}?id=${signupId}`
      : endpoints.admin.newsletter.getAll;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch newsletter signups');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching newsletter signups:', error);
    throw error;
  }
}

export async function updateNewsletterSignup(signupId, data) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.newsletter.update, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ id: signupId, ...data }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update newsletter signup');
    }

    return response.json();
  } catch (error) {
    console.error('Error updating newsletter signup:', error);
    throw error;
  }
}

export async function deleteNewsletterSignup(signupId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${endpoints.admin.newsletter.delete}?id=${signupId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete newsletter signup');
    }

    return response.json();
  } catch (error) {
    console.error('Error deleting newsletter signup:', error);
    throw error;
  }
}