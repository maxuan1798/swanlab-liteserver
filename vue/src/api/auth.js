import http from './http'

/**
 * Authentication API module
 */

export const authAPI = {
  /**
   * Login user
   * @param {string} email
   * @param {string} password
   * @returns {Promise}
   */
  login(email, password) {
    return http.post('/auth/login', { email, password })
  },

  /**
   * Register new user
   * @param {string} email
   * @param {string} password
   * @param {string} name
   * @returns {Promise}
   */
  register(email, password, name) {
    return http.post('/auth/register', { email, password, name })
  },

  /**
   * Refresh access token
   * @param {string} refreshToken
   * @returns {Promise}
   */
  refreshToken(refreshToken) {
    return http.post('/auth/refresh', { refresh_token: refreshToken })
  },

  /**
   * Logout user
   * @param {string} refreshToken
   * @returns {Promise}
   */
  logout(refreshToken) {
    return http.post('/auth/logout', { refresh_token: refreshToken })
  },

  /**
   * Get current user information
   * @returns {Promise}
   */
  getCurrentUser() {
    return http.get('/auth/me')
  },

  /**
   * Health check
   * @returns {Promise}
   */
  healthCheck() {
    return http.get('/auth/health')
  }
}

export default authAPI
