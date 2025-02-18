'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { auth, getIdTokenResult } from '@/config/firebase'
import { onAuthStateChanged } from 'firebase/auth'

const UserContext = createContext({
  user: null,
  loading: true,
})

export function UserProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isAdmin, setIsAdmin] = useState(false) 
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      try {
        if (firebaseUser) {
          const tokenResult = await getIdTokenResult()
          
          setUser({
            uid: firebaseUser.uid,
            email: firebaseUser.email,
            isAdmin: tokenResult?.claims?.admin || false,
            isSuperAdmin: tokenResult?.claims?.super_admin || false,
          })
          setIsAdmin(tokenResult?.claims?.admin || false)

        } else {
          setUser(null)
        }
      } catch (error) {
        console.error('Error getting user claims:', error)
        setUser(null)
      } finally {
        setLoading(false)
      }
    })

    return () => unsubscribe()
  }, [])



  return (
    <UserContext.Provider value={{ user, setUser,  loading, isAdmin, setIsAdmin }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  const context = useContext(UserContext)
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider')
  }
  return context
}
