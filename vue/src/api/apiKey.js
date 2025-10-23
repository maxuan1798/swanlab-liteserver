import http from './http'

/**
 * API Key management API module
 */

export const apiKeyAPI = {
  /**
   * Create a new API Key
   * @param {Object} params - API Key creation parameters
   * @param {string} params.name - API Key name
   * @param {string} [params.description] - API Key description
   * @param {string} [params.scope='read_write'] - Permission scope: read_only, read_write, admin
   * @param {number} [params.expires_in_days] - Expiration days (null for never)
   * @param {number} [params.rate_limit=1000] - Rate limit (requests/hour)
   * @returns {Promise}
   */
  create(params) {
    return http.post('/api-keys', params)
  },

  /**
   * List all API Keys for the current user
   * @returns {Promise}
   */
  list() {
    return http.get('/api-keys')
  },

  /**
   * Get API Key details
   * @param {string} apiKeyId - API Key ID
   * @returns {Promise}
   */
  get(apiKeyId) {
    return http.get(`/api-keys/${apiKeyId}`)
  },

  /**
   * Update API Key attributes
   * @param {string} apiKeyId - API Key ID
   * @param {Object} params - Update parameters
   * @param {string} [params.name] - New name
   * @param {string} [params.description] - New description
   * @param {string} [params.scope] - New scope: read_only, read_write, admin
   * @param {string} [params.status] - New status: active, inactive, revoked
   * @param {number} [params.rate_limit] - New rate limit
   * @returns {Promise}
   */
  update(apiKeyId, params) {
    return http.patch(`/api-keys/${apiKeyId}`, params)
  },

  /**
   * Revoke an API Key
   * @param {string} apiKeyId - API Key ID
   * @returns {Promise}
   */
  revoke(apiKeyId) {
    return http.delete(`/api-keys/${apiKeyId}`)
  }
}

export default apiKeyAPI
