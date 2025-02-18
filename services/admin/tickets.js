import { endpoints } from '@/config/endpoints';
import { getAdminToken } from '@/config/firebase';

// Public function
export async function createTicket(ticketData) {
  try {
    const response = await fetch(endpoints.admin.createTicket, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(ticketData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create ticket');
    }

    return response.json();
  } catch (error) {
    console.error('Error creating ticket:', error);
    throw error;
  }
}

// Admin functions
export async function getAllTickets() {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.getAllTickets, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch tickets');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching tickets:', error);
    throw error;
  }
}

export async function updateTicket(ticketId, ticketData) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.updateTicket, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ id: ticketId, ...ticketData }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update ticket');
    }

    return response.json();
  } catch (error) {
    console.error('Error updating ticket:', error);
    throw error;
  }
}

export async function deleteTicket(ticketId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${endpoints.admin.deleteTicket}?id=${ticketId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete ticket');
    }

    return response.json();
  } catch (error) {
    console.error('Error deleting ticket:', error);
    throw error;
  }
}

export async function createPdfTicket(ticketId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.createPdfTicket, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ ticket_id: ticketId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create PDF ticket');
    }

    return response.json();
  } catch (error) {
    console.error('Error creating PDF ticket:', error);
    throw error;
  }
}

export async function deletePdfTicket(ticketId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${endpoints.admin.deletePdfTicket}?ticket_id=${ticketId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete PDF ticket');
    }

    return response.json();
  } catch (error) {
    console.error('Error deleting PDF ticket:', error);
    throw error;
  }
}


export async function sendPdfTicket(ticketId) {
  try {
    const token = await getAdminToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(endpoints.admin.sendPdfTicket, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ ticket_id: ticketId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to send PDF ticket');
    }

    return response.json();
  } catch (error) {
    console.error('Error sending PDF ticket:', error);
    throw error;
  }
}

// New public function
export async function downloadPdfTicket(ticketId) {
  try {
    const response = await fetch(`${endpoints.downloadPdfTicket}?ticket_id=${ticketId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to download PDF ticket');
    }

    // Check if the response is JSON (error) or PDF
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to download PDF ticket');
    }

    // If it's not JSON, it should be the PDF file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `ticket_${ticketId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return { success: true, message: 'PDF ticket downloaded successfully' };
  } catch (error) {
    console.error('Error downloading PDF ticket:', error);
    throw error;
  }
}