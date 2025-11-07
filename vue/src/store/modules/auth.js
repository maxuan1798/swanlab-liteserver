import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@swanlab-vue/api/http'
import authAPI from '@swanlab-vue/api/auth'

export const useAuthStore = defineStore('auth', () => {
  /** state */
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const isLoading = ref(false)
  const error = ref(null)

  /** getters */
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const currentUser = computed(() => user.value)

  /** actions */

  /**
   * Set authentication tokens
   */
  const setTokens = (tokens) => {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token

    // Store in localStorage
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)

    // Set Authorization header for future requests
    http.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`
  }

  /**
   * Clear authentication data
   */
  const clearAuth = () => {
    user.value = null
    accessToken.value = null
    refreshToken.value = null

    // Remove from localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    // Remove Authorization header
    delete http.defaults.headers.common['Authorization']
  }

  /**
   * Login user with email and password
   */
  const login = async (email, password) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await authAPI.login(email, password)

      setTokens(response)

      // Get user info
      await getCurrentUser()

      return response
    } catch (err) {
      error.value = err.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register new user
   */
  const register = async (email, password, name) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await authAPI.register(email, password, name)

      setTokens(response)

      // Get user info
      await getCurrentUser()

      return response
    } catch (err) {
      error.value = err.data?.detail || 'Registration failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get current user information
   */
  const getCurrentUser = async () => {
    try {
      if (!accessToken.value) {
        return null
      }

      const response = await authAPI.getCurrentUser()
      user.value = response
      return response
    } catch (err) {
      // If unauthorized, clear auth data
      if (err.status === 401) {
        clearAuth()
      }
      throw err
    }
  }

  /**
   * Refresh access token
   */
  const refreshTokenRequest = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('No refresh token available')
      }

      const response = await authAPI.refreshToken(refreshToken.value)

      setTokens(response)
      return response
    } catch (err) {
      // If refresh fails, logout user
      clearAuth()
      throw err
    }
  }

  /**
   * Logout user
   */
  const logout = async () => {
    try {
      if (refreshToken.value) {
        await authAPI.logout(refreshToken.value)
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      clearAuth()
    }
  }

  /**
   * Initialize authentication state
   * Called on app startup
   */
  const initialize = async () => {
    if (accessToken.value) {
      try {
        // Set Authorization header
        http.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`

        // Get user info
        await getCurrentUser()
      } catch (err) {
        console.error('Auth initialization failed:', err)
        clearAuth()
      }
    }
  }

  return {
    // state
    user,
    accessToken,
    refreshToken,
    isLoading,
    error,

    // getters
    isAuthenticated,
    currentUser,

    // actions
    login,
    register,
    logout,
    getCurrentUser,
    refreshTokenRequest,
    initialize,
    clearAuth
  }
})
