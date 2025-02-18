import { endpoints } from '@/config/endpoints';
import { getAdminToken } from '@/config/firebase';

/**
 * Client-side service functions for event functionality
 */

// Public functions


// Admin functions
export async function createEvent(eventData) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.createEvent, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create event');
    }

    return response.json();
  } catch (error) {
    console.error('Error creating event:', error);
    throw error;
  }
}

export async function updateEvent(eventId, eventData) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.updateEvent, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ id: eventId, ...eventData }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update event');
    }

    return response.json();
  } catch (error) {
    console.error('Error updating event:', error);
    throw error;
  }
}

export async function deleteEvent(eventId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${endpoints.admin.deleteEvent}?id=${eventId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete event');
    }

    return response.json();
  } catch (error) {
    console.error('Error deleting event:', error);
    throw error;
  }
}

export async function getAllEventsAdmin() {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.getAllEventsAdmin, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch events');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching events:', error);
    throw error;
  }
}