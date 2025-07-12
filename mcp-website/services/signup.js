import { endpoints } from "../config/endpoints"

// Funzione per inviare la richiesta di iscrizione
export async function submitSignupRequest(formData) {
  try {
    const response = await fetch(endpoints.signupRequest, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    })

    let data = await response.json()

    // If the data is a JSON string, convert it to an object
    if (typeof data === "string") {
      data = JSON.parse(data)
    }

    if (!response.ok) {
      if (response.status === 409) {
        return { success: false, error: "This email is already registered." }
      }
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, data }
  } catch (error) {
    return { success: false, error: error.message }
  }
}

// CRUD per le domande

// Ottieni tutte le domande (endpoint pubblico)
export async function getQuestions() {
  try {
    const response = await fetch(endpoints.questions.getAll, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, questions: data }
  } catch (error) {
    console.error("Error fetching questions:", error)
    return { success: false, error: error.message }
  }
}

// Ottieni una domanda specifica per ID (solo admin)
export async function getQuestionById(questionId) {
  try {
    const response = await fetch(`${endpoints.admin.questions.getById}?id=${questionId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, question: data }
  } catch (error) {
    console.error(`Error fetching question with ID ${questionId}:`, error)
    return { success: false, error: error.message }
  }
}

// Crea una nuova domanda (solo admin)
export async function createQuestion(questionData) {
  try {
    const response = await fetch(endpoints.admin.questions.create, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(questionData),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, question: data }
  } catch (error) {
    console.error("Error creating question:", error)
    return { success: false, error: error.message }
  }
}

// Aggiorna una domanda esistente (solo admin)
export async function updateQuestion(questionId, questionData) {
  try {
    const response = await fetch(endpoints.admin.questions.update, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ id: questionId, ...questionData }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, question: data }
  } catch (error) {
    console.error(`Error updating question with ID ${questionId}:`, error)
    return { success: false, error: error.message }
  }
}

// Elimina una domanda (solo admin)
export async function deleteQuestion(questionId) {
  try {
    const response = await fetch(endpoints.admin.questions.delete, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ id: questionId }),
    })

    // Se la risposta è 204 No Content, non ci sarà un corpo JSON
    if (response.status === 204) {
      return { success: true }
    }

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true }
  } catch (error) {
    console.error(`Error deleting question with ID ${questionId}:`, error)
    return { success: false, error: error.message }
  }
}

// Riordina le domande (solo admin)
export async function reorderQuestions(questionsOrder) {
  try {
    const response = await fetch(endpoints.admin.questions.reorder, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ order: questionsOrder }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, questions: data }
  } catch (error) {
    console.error("Error reordering questions:", error)
    return { success: false, error: error.message }
  }
}

// Funzioni per le sottoscrizioni (tutte solo admin)

// Ottieni tutte le sottoscrizioni (solo admin)
export async function getSubscriptions(page = 1, limit = 20) {
  try {
    const response = await fetch(`${endpoints.admin.subscriptions.getAll}?page=${page}&limit=${limit}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return {
      success: true,
      subscriptions: data.subscriptions,
      pagination: data.pagination,
    }
  } catch (error) {
    console.error("Error fetching subscriptions:", error)
    return { success: false, error: error.message }
  }
}

// Ottieni una sottoscrizione specifica per ID (solo admin)
export async function getSubscriptionById(subscriptionId) {
  try {
    const response = await fetch(`${endpoints.admin.subscriptions.getById}?id=${subscriptionId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, subscription: data }
  } catch (error) {
    console.error(`Error fetching subscription with ID ${subscriptionId}:`, error)
    return { success: false, error: error.message }
  }
}

// Aggiorna lo stato di una sottoscrizione (solo admin)
export async function updateSubscriptionStatus(subscriptionId, status, notes = "") {
  try {
    const response = await fetch(endpoints.admin.subscriptions.updateStatus, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ id: subscriptionId, status, notes }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true, subscription: data }
  } catch (error) {
    console.error(`Error updating subscription status for ID ${subscriptionId}:`, error)
    return { success: false, error: error.message }
  }
}

// Elimina una sottoscrizione (solo admin)
export async function deleteSubscription(subscriptionId) {
  try {
    const response = await fetch(endpoints.admin.subscriptions.delete, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ id: subscriptionId }),
    })

    // Se la risposta è 204 No Content, non ci sarà un corpo JSON
    if (response.status === 204) {
      return { success: true }
    }

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }

    return { success: true }
  } catch (error) {
    console.error(`Error deleting subscription with ID ${subscriptionId}:`, error)
    return { success: false, error: error.message }
  }
}

// Esporta le sottoscrizioni in formato CSV (solo admin)
export async function exportSubscriptionsToCSV(filters = {}) {
  try {
    const queryParams = new URLSearchParams(filters).toString()
    const response = await fetch(`${endpoints.admin.subscriptions.export}?${queryParams}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    // Ottieni il blob del file CSV
    const blob = await response.blob()

    // Crea un URL per il blob
    const url = window.URL.createObjectURL(blob)

    // Crea un elemento <a> per scaricare il file
    const a = document.createElement("a")
    a.style.display = "none"
    a.href = url
    a.download = `subscriptions-export-${new Date().toISOString().split("T")[0]}.csv`

    // Aggiungi l'elemento al DOM e simula un click
    document.body.appendChild(a)
    a.click()

    // Pulisci
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    return { success: true }
  } catch (error) {
    console.error("Error exporting subscriptions:", error)
    return { success: false, error: error.message }
  }
}

