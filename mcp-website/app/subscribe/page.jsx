"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react"
import Link from "next/link"
import { submitSignupRequest, getQuestions } from "@/services/signup"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CheckCircle, XCircle } from "lucide-react"
import { AnimatedBackground } from "@/components/AnimatedBackground"

export default function SubscribePage() {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [currentAnswer, setCurrentAnswer] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false)
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [isValid, setIsValid] = useState(false)
  const [questions, setQuestions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)

  // Refs per i campi della data
  const dayInputRef = useRef(null)
  const monthInputRef = useRef(null)
  const yearInputRef = useRef(null)

  // Stati per i campi della data
  const [dateFields, setDateFields] = useState({
    day: "",
    month: "",
    year: "",
  })

  const currentQuestion = questions[currentQuestionIndex]

  // Calcola la data massima (18 anni fa da oggi)
  const maxDate = new Date()
  maxDate.setFullYear(maxDate.getFullYear() - 18)

  // Calcola la data minima (anno 1950)
  const minDate = new Date(1950, 0, 1)

  // 1. Add a function to format dates in day-month-year format
  const formatDateDMY = (date) => {
    if (!date) return ""
    const day = date.getDate().toString().padStart(2, "0")
    const month = (date.getMonth() + 1).toString().padStart(2, "0")
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  // 2. Update the useEffect that fetches questions to sort them by order field
  useEffect(() => {
    fetchQuestions()
  }, [])

  async function fetchQuestions() {
    setIsLoading(true)
    setFetchError(false)

    try {
      const response = await getQuestions()

      if (response.success && response.questions && response.questions.length > 0) {
        // Sort questions by order field
        const sortedQuestions = [...response.questions].sort((a, b) => {
          // If both have order field, sort by order
          if (a.order !== undefined && b.order !== undefined) {
            return a.order - b.order
          }
          // If only a has order, a comes first
          if (a.order !== undefined) {
            return -1
          }
          // If only b has order, b comes first
          if (b.order !== undefined) {
            return 1
          }
          // If neither has order, maintain original order
          return 0
        })

        setQuestions(sortedQuestions)
      } else {
        throw new Error(response.error || "Failed to fetch questions")
      }
    } catch (error) {
      console.error("Error fetching questions:", error)
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }

  // Validazione dell'input corrente
  useEffect(() => {
    if (!currentQuestion) return

    if (currentQuestion.input === "date") {
      // Per le date, controlliamo se tutti i campi sono validi
      const { day, month, year } = dateFields

      // Verifica se tutti i campi sono compilati
      if (!day || !month || !year) {
        setIsValid(false)
        return
      }

      // Converti in numeri
      const dayNum = Number.parseInt(day, 10)
      const monthNum = Number.parseInt(month, 10)
      const yearNum = Number.parseInt(year, 10)

      // Verifica se i valori sono nel range corretto
      if (
        isNaN(dayNum) ||
        isNaN(monthNum) ||
        isNaN(yearNum) ||
        dayNum < 1 ||
        dayNum > 31 ||
        monthNum < 1 ||
        monthNum > 12 ||
        yearNum < 1950 ||
        yearNum > new Date().getFullYear() - 18
      ) {
        setIsValid(false)
        return
      }

      // Verifica se la data è valida (es. 30 febbraio non esiste)
      const date = new Date(yearNum, monthNum - 1, dayNum)
      if (date.getDate() !== dayNum || date.getMonth() !== monthNum - 1 || date.getFullYear() !== yearNum) {
        setIsValid(false)
        return
      }

      // Se arriviamo qui, la data è valida
      setIsValid(true)
      return
    }

    let valid = currentAnswer !== ""

    if (currentQuestion.required && !currentAnswer) {
      valid = false
    }

    if (currentQuestion.input === "email" && currentAnswer) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      valid = emailRegex.test(currentAnswer)
    }

    if (currentQuestion.input === "number" && currentAnswer) {
      const num = Number(currentAnswer)
      valid =
        !isNaN(num) &&
        (currentQuestion.min === undefined || num >= currentQuestion.min) &&
        (currentQuestion.max === undefined || num <= currentQuestion.max)
    }

    setIsValid(valid)
  }, [currentAnswer, dateFields, currentQuestion])

  // Imposta la risposta corrente quando cambia la domanda
  useEffect(() => {
    if (!currentQuestion) return

    if (currentQuestion.input === "date") {
      // Se c'è già una risposta per questa domanda, popola i campi
      const savedDate = answers[currentQuestion.id]
      if (savedDate) {
        setDateFields({
          day: savedDate.getDate().toString().padStart(2, "0"),
          month: (savedDate.getMonth() + 1).toString().padStart(2, "0"),
          year: savedDate.getFullYear().toString(),
        })
      } else {
        // Altrimenti, resetta i campi
        setDateFields({ day: "", month: "", year: "" })
      }
    } else {
      setCurrentAnswer(answers[currentQuestion.id] || "")
    }
  }, [currentQuestionIndex, answers, currentQuestion])

  const handleInputChange = (e) => {
    setCurrentAnswer(e.target.value)
  }

  // Gestisce il cambio dei campi della data
  const handleDateFieldChange = (field, value) => {
    // Rimuovi caratteri non numerici
    const numericValue = value.replace(/\D/g, "")

    // Limita la lunghezza in base al campo
    const maxLength = field === "year" ? 4 : 2
    const trimmedValue = numericValue.slice(0, maxLength)

    // Aggiorna lo stato
    const newDateFields = {
      ...dateFields,
      [field]: trimmedValue,
    }

    setDateFields(newDateFields)

    // Gestisci il focus automatico al campo successivo
    if (field === "day" && trimmedValue.length === 2) {
      monthInputRef.current?.focus()
    } else if (field === "month" && trimmedValue.length === 2) {
      yearInputRef.current?.focus()
    }

    // Aggiorna answers se tutti i campi sono validi
    const { day, month, year } = newDateFields
    if (day && month && year && year.length === 4) {
      const dayNum = Number.parseInt(day, 10)
      const monthNum = Number.parseInt(month, 10)
      const yearNum = Number.parseInt(year, 10)

      // Verifica validità base
      if (
        !isNaN(dayNum) &&
        !isNaN(monthNum) &&
        !isNaN(yearNum) &&
        dayNum >= 1 &&
        dayNum <= 31 &&
        monthNum >= 1 &&
        monthNum <= 12 &&
        yearNum >= 1950 &&
        yearNum <= new Date().getFullYear() - 18
      ) {
        // Verifica data valida
        const date = new Date(yearNum, monthNum - 1, dayNum)
        if (date.getDate() === dayNum && date.getMonth() === monthNum - 1 && date.getFullYear() === yearNum) {
          // Aggiorna answers con la data completa
          setAnswers((prev) => ({
            ...prev,
            [currentQuestion.id]: date,
          }))
        }
      }
    }
  }

  // Gestisce il tasto backspace nei campi della data
  const handleDateKeyDown = (field, e) => {
    // Se è backspace e il campo è vuoto, torna al campo precedente
    if (e.key === "Backspace" && !dateFields[field]) {
      if (field === "year") {
        monthInputRef.current?.focus()
      } else if (field === "month") {
        dayInputRef.current?.focus()
      }
    } else if (e.key === "Enter" && isValid) {
      handleNext()
    }
  }

  const handleNext = () => {
    if (!isValid) return

    // Salva la risposta corrente (solo per input non-date)
    if (currentQuestion.input !== "date") {
      // Aggiorna lo stato answers con la risposta corrente
      setAnswers((prev) => ({
        ...prev,
        [currentQuestion.id]: currentAnswer,
      }))

      // Se è l'ultima domanda, invia il form dopo aver aggiornato lo stato
      if (currentQuestionIndex === questions.length - 1) {
        // Crea una copia aggiornata delle risposte che include la risposta corrente
        const updatedAnswers = {
          ...answers,
          [currentQuestion.id]: currentAnswer,
        }

        // Passa le risposte aggiornate alla funzione handleSubmit
        handleSubmit(updatedAnswers)
        return
      }
    } else {
      // Se è l'ultima domanda, invia il form
      if (currentQuestionIndex === questions.length - 1) {
        handleSubmit(answers)
        return
      }
    }

    // Altrimenti, passa alla domanda successiva
    setCurrentQuestionIndex((prev) => prev + 1)
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && isValid) {
      e.preventDefault()
      handleNext()
    }
  }

  // Funzione per gestire i messaggi di errore in modo user-friendly
  const handleErrorMessage = (error) => {
    // Se c'è un messaggio specifico dal server, usalo
    if (error && typeof error === "object" && error.message) {
      return error.message
    }

    // Se è una stringa che contiene "HTTP error", sostituiscila con un messaggio generico
    if (typeof error === "string" && error.includes("HTTP error")) {
      return "We're sorry, but we couldn't process your application at this time. Please try again later."
    }

    // Se è una stringa che contiene "email is already registered"
    if (typeof error === "string" && error.toLowerCase().includes("email is already registered")) {
      return "This email address is already registered in our system."
    }

    // Messaggio generico per altri errori
    return "We're sorry, but we couldn't process your application at this time. Please try again later."
  }

  // 3. Update the handleSubmit function to format dates in day-month-year format
  const handleSubmit = async (submittedAnswers = answers) => {
    setIsSubmitting(true)

    // Prepara i dati per l'invio
    const formattedAnswers = {}
    const questionsList = []

    questions.forEach((q) => {
      let answer = submittedAnswers[q.id] || ""

      // Formatta la data se necessario
      if (q.input === "date" && submittedAnswers[q.id]) {
        answer = formatDateDMY(submittedAnswers[q.id])
      }

      // Se la domanda ha un varName, la mappa direttamente
      if (q.varName) {
        // Assicurati che l'email non sia vuota se è richiesta
        if (q.varName === "email" && q.required && (!answer || answer.trim() === "")) {
          setErrorMessage("Email is required")
          setIsErrorModalOpen(true)
          setIsSubmitting(false)
          return
        }

        formattedAnswers[q.varName] = q.input === "number" ? Number(answer) : answer
      } else {
        // Altrimenti, la aggiunge all'array delle domande
        questionsList.push({
          question: q.question,
          answer: answer,
        })
      }
    })

    // Verifica che l'email sia presente e valida
    if (!formattedAnswers.email || formattedAnswers.email.trim() === "") {
      // Cerca una domanda con input di tipo email
      const emailQuestion = questions.find((q) => q.input === "email")
      if (emailQuestion) {
        const emailAnswer = submittedAnswers[emailQuestion.id] || ""
        if (emailAnswer && emailAnswer.trim() !== "") {
          formattedAnswers.email = emailAnswer
        }
      }
    }

    // Aggiunge l'array delle domande
    formattedAnswers.questions = questionsList

    try {
      const result = await submitSignupRequest(formattedAnswers)

      if (result.success) {
        setIsSuccessModalOpen(true)
      } else {
        // Usa la funzione per ottenere un messaggio di errore user-friendly
        const userFriendlyError = result.message || result.error
        setErrorMessage(handleErrorMessage(userFriendlyError))
        setIsErrorModalOpen(true)
      }
    } catch (error) {
      console.error("Signup error:", error)
      // Usa la funzione per ottenere un messaggio di errore user-friendly
      setErrorMessage(handleErrorMessage(error))
      setIsErrorModalOpen(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Stili personalizzati per i campi della data
  const dateFieldsStyles = `
    .date-field {
      background-color: transparent;
      border: none;
      border-bottom: 1px solid rgba(255, 107, 0, 0.3);
      color: white;
      font-size: 1.25rem;
      padding: 0.5rem 0;
      text-align: center;
      width: 100%;
      outline: none;
    }
    
    .date-field:focus {
      border-bottom-color: rgba(255, 107, 0, 0.7);
    }
    
    .date-field::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
    
    .date-separator {
      color: rgba(255, 255, 255, 0.5);
      font-size: 1.5rem;
      margin: 0 0.5rem;
    }
    
    .date-label {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.75rem;
      margin-bottom: 0.25rem;
      text-align: center;
    }
    
    .date-fields-container {
      display: flex;
      align-items: flex-end;
      justify-content: center;
      margin-top: 1rem;
    }
    
    .date-field-group {
      display: flex;
      flex-direction: column;
    }
    
    .enter-hint {
      color: rgba(255, 255, 255, 0.5);
      font-size: 0.75rem;
      margin-left: 0.5rem;
    }
  `

  // Se c'è un errore nel caricamento delle domande, mostra un messaggio di errore
  if (fetchError) {
    return (
      <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center">
        <AnimatedBackground />
        <div className="z-10 text-center max-w-md px-4">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">Unable to load subscription form</h2>
          <p className="text-gray-400 mb-8">
            We're sorry, but it's not possible to join the community at the moment. Please try again later.
          </p>
          <Link href="/">
            <Button className="bg-mcp-orange hover:bg-mcp-orange/90 text-black">Return to Home</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center relative">
      {/* Content */}
      <AnimatedBackground />

      {/* Stili personalizzati per i campi della data */}
      <style jsx global>
        {dateFieldsStyles}
      </style>

      <div className="container mx-auto px-4 z-10 max-w-xl">
        {isLoading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 text-mcp-orange animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading questions...</p>
          </div>
        ) : (
          <>
            <div className="text-center mb-8">
              <div className="text-sm text-gray-400 mb-2">
                Question {currentQuestionIndex + 1} of {questions.length}
              </div>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={currentQuestionIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div className="text-center">
                  <h2 className="text-2xl md:text-3xl font-helvetica text-white mb-2">
                    <span className="text-mcp-orange">{currentQuestionIndex + 1}.</span> {currentQuestion.question}
                  </h2>
                  <p className="text-sm text-gray-400">{currentQuestion.note}</p>
                </div>

                <div className="mt-6 flex justify-center">
                  <div className="w-full max-w-md">
                    {currentQuestion.input === "string" && (
                      <input
                        value={currentAnswer}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        placeholder={currentQuestion.placeholder}
                        className="w-full h-12 text-base bg-transparent border-0 border-b border-mcp-orange/30 text-white focus:border-mcp-orange/70 focus:outline-none focus:ring-0 px-0"
                        autoFocus
                      />
                    )}

                    {currentQuestion.input === "email" && (
                      <input
                        type="email"
                        value={currentAnswer}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        placeholder={currentQuestion.placeholder}
                        className="w-full h-12 text-base bg-transparent border-0 border-b border-mcp-orange/30 text-white focus:border-mcp-orange/70 focus:outline-none focus:ring-0 px-0"
                        autoFocus
                      />
                    )}

                    {currentQuestion.input === "number" && (
                      <input
                        type="number"
                        value={currentAnswer}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        placeholder={currentQuestion.placeholder}
                        min={currentQuestion.min}
                        max={currentQuestion.max}
                        className="w-full h-12 text-base bg-transparent border-0 border-b border-mcp-orange/30 text-white focus:border-mcp-orange/70 focus:outline-none focus:ring-0 px-0"
                        autoFocus
                      />
                    )}

                    {currentQuestion.input === "date" && (
                      <div className="flex flex-col items-center">
                        <div className="date-fields-container">
                          <div className="date-field-group">
                            <div className="date-label">Day</div>
                            <input
                              ref={dayInputRef}
                              type="text"
                              value={dateFields.day}
                              onChange={(e) => handleDateFieldChange("day", e.target.value)}
                              onKeyDown={(e) => handleDateKeyDown("day", e)}
                              placeholder="DD"
                              className="date-field"
                              maxLength={2}
                              autoFocus
                            />
                          </div>

                          <span className="date-separator">/</span>

                          <div className="date-field-group">
                            <div className="date-label">Month</div>
                            <input
                              ref={monthInputRef}
                              type="text"
                              value={dateFields.month}
                              onChange={(e) => handleDateFieldChange("month", e.target.value)}
                              onKeyDown={(e) => handleDateKeyDown("month", e)}
                              placeholder="MM"
                              className="date-field"
                              maxLength={2}
                            />
                          </div>

                          <span className="date-separator">/</span>

                          <div className="date-field-group">
                            <div className="date-label">Year</div>
                            <input
                              ref={yearInputRef}
                              type="text"
                              value={dateFields.year}
                              onChange={(e) => handleDateFieldChange("year", e.target.value)}
                              onKeyDown={(e) => handleDateKeyDown("year", e)}
                              placeholder="YYYY"
                              className="date-field"
                              maxLength={4}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>

            <div className="flex justify-between mt-12">
              <Button
                type="button"
                onClick={handlePrevious}
                disabled={currentQuestionIndex === 0}
                variant="ghost"
                className="text-gray-500 hover:text-white hover:bg-transparent"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>

              <Button
                type="button"
                onClick={handleNext}
                disabled={!isValid || isSubmitting}
                className="bg-gray-700 hover:bg-gray-600 text-white px-6"
              >
                {isSubmitting ? (
                  <div className="flex items-center">
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Submitting...
                  </div>
                ) : currentQuestionIndex === questions.length - 1 ? (
                  "Submit"
                ) : (
                  <>
                    Next
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>

            <div className="mt-8 text-center">
              <Link
                href="/"
                className="text-xs text-gray-500 hover:text-mcp-orange transition-colors inline-flex items-center"
              >
                <ArrowLeft className="w-3 h-3 mr-1" />
                Return to Home Page
              </Link>
            </div>
          </>
        )}
      </div>

      {/* Success Modal */}
      <Dialog open={isSuccessModalOpen} onOpenChange={setIsSuccessModalOpen}>
        <DialogContent className="bg-black border border-mcp-orange/50 text-white max-w-[90vw] md:max-w-md p-6">
          <DialogHeader>
            <DialogTitle className="dialog-title gradient-text flex items-center">
              <CheckCircle className="w-6 h-6 mr-2 text-green-500" />
              <span className="tracking-wider">APPLICATION SUBMITTED</span>
            </DialogTitle>
            <DialogDescription className="text-base text-gray-300 font-light">
              Thank you for your interest in joining the Music Connecting People community. We have received your
              application and our team will review it shortly. You will receive an email with further information soon.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Link href="/">
              <Button className="w-full bg-mcp-orange hover:bg-mcp-orange/90 text-black font-light">
                Return to Home
              </Button>
            </Link>
          </div>
        </DialogContent>
      </Dialog>

      {/* Error Modal */}
      <Dialog open={isErrorModalOpen} onOpenChange={setIsErrorModalOpen}>
        <DialogContent className="bg-black border border-mcp-orange/50 text-white max-w-[90vw] md:max-w-md p-6">
          <DialogHeader>
            <DialogTitle className="dialog-title text-red-500 flex items-center">
              <XCircle className="w-6 h-6 mr-2" />
              <span className="tracking-wider">Unable to Complete Registration</span>
            </DialogTitle>
            <DialogDescription className="text-base text-gray-300 font-light">{errorMessage}</DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Button
              onClick={() => setIsErrorModalOpen(false)}
              className="w-full bg-mcp-orange hover:bg-mcp-orange/90 text-black font-light"
            >
              Try Again
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

