'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { apiClient } from '@/lib/api'
import { createStore, useStore } from 'zustand'

interface User {
  id: string
  email: string
  name: string
  plan: string
  auth_provider?: 'email' | 'google'
  google_connected?: boolean
  preferences?: {
    language?: 'zh' | 'en' | 'system'
  }
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
  updateUserPreferences: (preferences: { language?: 'zh' | 'en' | 'system' }) => Promise<void>
  updateProfile: (profile: { name?: string }) => Promise<void>
  setPassword: (newPassword: string) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  deleteAccount: () => Promise<void>
}

const authStore = createStore<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  login: async (token) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('token', token)
        console.log('Token stored successfully in localStorage')
      } else {
        console.warn('localStorage not available during login')
      }
    } catch (error) {
      console.error('Failed to store token in localStorage:', error)
    }
    
    set({ token, isAuthenticated: true })
    await get().loadUser()
  },
  logout: () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('token')
        localStorage.removeItem('userPreferences')
        console.log('Cleared tokens from localStorage')
      } else {
        console.warn('localStorage not available during logout')
      }
    } catch (error) {
      console.error('Failed to clear tokens from localStorage:', error)
    }
    
    set({ user: null, token: null, isAuthenticated: false })
  },
  loadUser: async () => {
    let token = get().token
    
    if (!token) {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          token = localStorage.getItem('token')
        }
      } catch (error) {
        console.error('Failed to access localStorage in loadUser:', error)
      }
    }
    
    console.log('Loading user with token:', token ? 'present' : 'missing')
    
    if (token) {
      try {
        // Set token for API calls
        set({ token })
        
        console.log('Calling getUserProfile API...')
        const user = await apiClient.getUserProfile()
        console.log('User profile loaded:', user?.name || 'No name', user?.email || 'No email')
        
        set({ user, isAuthenticated: true, isLoading: false })
        
        // Apply user preferences if they exist
        if (user.preferences) {
          try {
            if (typeof window !== 'undefined' && window.localStorage) {
              localStorage.setItem('userPreferences', JSON.stringify(user.preferences))
              
              // Apply language preference only (theme stays local)
              if (user.preferences.language) {
                localStorage.setItem('language', user.preferences.language)
                // Trigger language change event
                window.dispatchEvent(new CustomEvent('languageChange', { detail: user.preferences.language }))
              }
            }
          } catch (error) {
            console.error('Failed to store user preferences in localStorage:', error)
          }
        }
        
      } catch (error) {
        console.error('Failed to load user:', error)
        console.error('Error details:', error instanceof Error ? error.message : error)
        get().logout()
        set({ isLoading: false })
      }
    } else {
      console.log('No token found, setting not authenticated')
      set({ isLoading: false })
    }
  },
  updateUserPreferences: async (preferences) => {
    const currentUser = get().user
    if (!currentUser) return
    
    try {
      await apiClient.updateUserPreferences(preferences)
      
      // Update local state
      const updatedUser = {
        ...currentUser,
        preferences: { ...currentUser.preferences, ...preferences }
      }
      set({ user: updatedUser })
      
      // Update localStorage safely
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          localStorage.setItem('userPreferences', JSON.stringify(updatedUser.preferences))
          
          // Apply language preference immediately (theme stays local)
          if (preferences.language) {
            localStorage.setItem('language', preferences.language)
            window.dispatchEvent(new CustomEvent('languageChange', { detail: preferences.language }))
          }
        }
      } catch (error) {
        console.error('Failed to update localStorage in updateUserPreferences:', error)
      }
      
    } catch (error) {
      console.error('Failed to update user preferences', error)
      throw error
    }
  },
  updateProfile: async (profile) => {
    const currentUser = get().user
    if (!currentUser) return
    
    try {
      const updatedUser = await apiClient.updateProfile(profile)
      set({ user: updatedUser })
    } catch (error) {
      console.error('Failed to update profile', error)
      throw error
    }
  },
  setPassword: async (newPassword) => {
    try {
      await apiClient.setPassword(newPassword)
    } catch (error) {
      console.error('Failed to set password', error)
      throw error
    }
  },
  changePassword: async (currentPassword, newPassword) => {
    try {
      await apiClient.changePassword(currentPassword, newPassword)
    } catch (error) {
      console.error('Failed to change password', error)
      throw error
    }
  },
  deleteAccount: async () => {
    try {
      await apiClient.deleteAccount()
      get().logout()
    } catch (error) {
      console.error('Failed to delete account', error)
      throw error
    }
  },
}))

const AuthContext = createContext<typeof authStore | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    let token: string | null = null
    
    // Safe localStorage access with error handling
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        token = localStorage.getItem('token')
        console.log('AuthProvider: Retrieved token from localStorage:', token ? 'present' : 'missing')
      } else {
        console.log('AuthProvider: localStorage not available')
      }
    } catch (error) {
      console.error('AuthProvider: Failed to access localStorage:', error)
    }
    
    if (token) {
      console.log('AuthProvider: Attempting login with existing token')
      authStore.getState().login(token)
    } else {
      console.log('AuthProvider: No token found, setting not loading')
      authStore.setState({ isLoading: false })
    }
  }, [])

  return (
    <AuthContext.Provider value={authStore}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const store = useContext(AuthContext)
  if (!store) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return useStore(store)
}
