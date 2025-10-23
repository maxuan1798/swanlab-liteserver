<template>
  <div class="api-keys-container">
    <!-- Header -->
    <div class="header">
      <div>
        <h1 class="text-2xl font-bold text-default">{{ $t('settings.apiKeys.title', 'API Keys') }}</h1>
        <p class="text-dimmer text-sm mt-2">
          {{ $t('settings.apiKeys.description', 'Manage your API keys for programmatic access to SwanLab') }}
        </p>
      </div>
      <button @click="showCreateDialog = true" class="btn-primary">
        <SLIcon icon="plus" class="w-4 h-4 mr-2" />
        {{ $t('settings.apiKeys.create', 'Create API Key') }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div v-for="i in 3" :key="i" class="skeleton-card"></div>
    </div>

    <!-- API Keys List -->
    <div v-else-if="apiKeys.length > 0" class="api-keys-list">
      <div v-for="apiKey in apiKeys" :key="apiKey.id" class="api-key-card">
        <div class="card-header">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-semibold text-default">{{ apiKey.name }}</h3>
              <span :class="getStatusClass(apiKey.status)" class="status-badge">
                {{ apiKey.status }}
              </span>
            </div>
            <p v-if="apiKey.description" class="text-dimmer text-sm mt-1">{{ apiKey.description }}</p>
          </div>
          <div class="card-actions">
            <button @click="editApiKey(apiKey)" class="btn-icon" :title="$t('common.edit', 'Edit')">
              <SLIcon icon="edit" class="w-4 h-4" />
            </button>
            <button @click="confirmRevoke(apiKey)" class="btn-icon btn-danger" :title="$t('common.delete', 'Delete')">
              <SLIcon icon="trash" class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('settings.apiKeys.keyId', 'Key ID') }}</span>
              <span class="info-value font-mono">{{ apiKey.key_id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('settings.apiKeys.scope', 'Scope') }}</span>
              <span class="info-value">{{ apiKey.scope }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('settings.apiKeys.rateLimit', 'Rate Limit') }}</span>
              <span class="info-value">{{ apiKey.rate_limit }} req/h</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('settings.apiKeys.usageCount', 'Usage Count') }}</span>
              <span class="info-value">{{ apiKey.usage_count }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('settings.apiKeys.created', 'Created') }}</span>
              <span class="info-value">{{ formatDate(apiKey.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('settings.apiKeys.lastUsed', 'Last Used') }}</span>
              <span class="info-value">{{ apiKey.last_used_at ? formatDate(apiKey.last_used_at) : 'Never' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <SLIcon icon="key" class="w-16 h-16 text-dimmest" />
      <p class="text-dimmer text-lg mt-4">{{ $t('settings.apiKeys.empty.title', 'No API Keys') }}</p>
      <p class="text-dimmest text-sm mt-2">
        {{ $t('settings.apiKeys.empty.description', 'Create an API key to access SwanLab programmatically') }}
      </p>
      <button @click="showCreateDialog = true" class="btn-primary mt-4">
        {{ $t('settings.apiKeys.create', 'Create API Key') }}
      </button>
    </div>

    <!-- Create/Edit Dialog -->
    <Teleport to="body">
      <div v-if="showCreateDialog || showEditDialog" class="modal-overlay" @click.self="closeDialogs">
        <div class="modal-content">
          <div class="modal-header">
            <h2 class="text-xl font-bold text-default">
              {{ showEditDialog ? $t('settings.apiKeys.edit', 'Edit API Key') : $t('settings.apiKeys.create', 'Create API Key') }}
            </h2>
            <button @click="closeDialogs" class="btn-icon">
              <SLIcon icon="close" class="w-5 h-5" />
            </button>
          </div>

          <div class="modal-body">
            <!-- Show created key only once -->
            <div v-if="createdKeySecret" class="alert alert-warning mb-4">
              <div class="flex items-start gap-3">
                <SLIcon icon="warning" class="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div class="flex-1">
                  <p class="font-semibold mb-2">
                    {{ $t('settings.apiKeys.secretWarning', 'Save your API key - you won\'t see it again!') }}
                  </p>
                  <div class="secret-container">
                    <code class="secret-code">{{ createdKeySecret }}</code>
                    <button @click="copySecret" class="btn-copy">
                      <SLIcon :icon="secretCopied ? 'check' : 'copy'" class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <form @submit.prevent="submitForm" class="form">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.apiKeys.name', 'Name') }} *</label>
                <input
                  v-model="formData.name"
                  type="text"
                  class="form-input"
                  :placeholder="$t('settings.apiKeys.namePlaceholder', 'My API Key')"
                  required
                />
              </div>

              <div class="form-group">
                <label class="form-label">{{ $t('settings.apiKeys.description', 'Description') }}</label>
                <textarea
                  v-model="formData.description"
                  class="form-input"
                  rows="3"
                  :placeholder="$t('settings.apiKeys.descriptionPlaceholder', 'API Key for...')"
                ></textarea>
              </div>

              <div class="form-group">
                <label class="form-label">{{ $t('settings.apiKeys.scope', 'Scope') }} *</label>
                <select v-model="formData.scope" class="form-input" required>
                  <option value="read_only">Read Only</option>
                  <option value="read_write">Read & Write</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div v-if="showEditDialog" class="form-group">
                <label class="form-label">{{ $t('settings.apiKeys.status', 'Status') }}</label>
                <select v-model="formData.status" class="form-input">
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">{{ $t('settings.apiKeys.rateLimit', 'Rate Limit (requests/hour)') }}</label>
                <input
                  v-model.number="formData.rate_limit"
                  type="number"
                  class="form-input"
                  min="1"
                  :placeholder="'1000'"
                />
              </div>

              <div v-if="!showEditDialog" class="form-group">
                <label class="form-label">{{ $t('settings.apiKeys.expiresIn', 'Expires In (days)') }}</label>
                <input
                  v-model.number="formData.expires_in_days"
                  type="number"
                  class="form-input"
                  min="1"
                  :placeholder="$t('settings.apiKeys.neverExpires', 'Leave empty for never')"
                />
              </div>

              <div class="form-actions">
                <button type="button" @click="closeDialogs" class="btn-secondary">
                  {{ $t('common.cancel', 'Cancel') }}
                </button>
                <button type="submit" class="btn-primary" :disabled="submitting">
                  {{ submitting ? $t('common.saving', 'Saving...') : $t('common.save', 'Save') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Revoke Confirmation Dialog -->
    <Teleport to="body">
      <div v-if="showRevokeDialog" class="modal-overlay" @click.self="showRevokeDialog = false">
        <div class="modal-content modal-sm">
          <div class="modal-header">
            <h2 class="text-xl font-bold text-default">
              {{ $t('settings.apiKeys.revokeTitle', 'Revoke API Key') }}
            </h2>
          </div>
          <div class="modal-body">
            <p class="text-dimmer mb-4">
              {{ $t('settings.apiKeys.revokeConfirm', 'Are you sure you want to revoke this API key? This action cannot be undone.') }}
            </p>
            <div class="form-actions">
              <button @click="showRevokeDialog = false" class="btn-secondary">
                {{ $t('common.cancel', 'Cancel') }}
              </button>
              <button @click="revokeApiKey" class="btn-danger" :disabled="submitting">
                {{ submitting ? $t('common.deleting', 'Deleting...') : $t('common.delete', 'Delete') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
/**
 * @description: API Keys management view
 * @file: ApiKeysView.vue
 * @since: 2025-01-23
 **/
import { ref, onMounted } from 'vue'
import { apiKeyAPI } from '@swanlab-vue/api/apiKey'
import SLIcon from '@swanlab-vue/components/SLIcon.vue'

const loading = ref(true)
const submitting = ref(false)
const apiKeys = ref([])

// Dialog states
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showRevokeDialog = ref(false)

// Form data
const formData = ref({
  name: '',
  description: '',
  scope: 'read_write',
  status: 'active',
  rate_limit: 1000,
  expires_in_days: null
})

// Created key secret (only shown once)
const createdKeySecret = ref(null)
const secretCopied = ref(false)

// Current editing/revoking key
const currentApiKey = ref(null)

// Load API keys
const loadApiKeys = async () => {
  try {
    loading.value = true
    const response = await apiKeyAPI.list()
    apiKeys.value = response.data?.api_keys || []
  } catch (error) {
    console.error('Failed to load API keys:', error)
    // TODO: Show error notification
  } finally {
    loading.value = false
  }
}

// Submit form (create or edit)
const submitForm = async () => {
  try {
    submitting.value = true

    if (showEditDialog.value && currentApiKey.value) {
      // Update existing key
      const response = await apiKeyAPI.update(currentApiKey.value.id, formData.value)
      const index = apiKeys.value.findIndex(k => k.id === currentApiKey.value.id)
      if (index !== -1) {
        apiKeys.value[index] = response.data
      }
    } else {
      // Create new key
      const response = await apiKeyAPI.create(formData.value)
      createdKeySecret.value = response.data?.api_key?.key_secret
      // Reload list to get the new key
      await loadApiKeys()
      // Keep dialog open to show the secret
      if (!createdKeySecret.value) {
        closeDialogs()
      }
      return
    }

    closeDialogs()
  } catch (error) {
    console.error('Failed to save API key:', error)
    // TODO: Show error notification
  } finally {
    submitting.value = false
  }
}

// Edit API key
const editApiKey = (apiKey) => {
  currentApiKey.value = apiKey
  formData.value = {
    name: apiKey.name,
    description: apiKey.description || '',
    scope: apiKey.scope,
    status: apiKey.status,
    rate_limit: apiKey.rate_limit
  }
  showEditDialog.value = true
}

// Confirm revoke
const confirmRevoke = (apiKey) => {
  currentApiKey.value = apiKey
  showRevokeDialog.value = true
}

// Revoke API key
const revokeApiKey = async () => {
  try {
    submitting.value = true
    await apiKeyAPI.revoke(currentApiKey.value.id)
    apiKeys.value = apiKeys.value.filter(k => k.id !== currentApiKey.value.id)
    showRevokeDialog.value = false
    currentApiKey.value = null
  } catch (error) {
    console.error('Failed to revoke API key:', error)
    // TODO: Show error notification
  } finally {
    submitting.value = false
  }
}

// Copy secret to clipboard
const copySecret = async () => {
  try {
    await navigator.clipboard.writeText(createdKeySecret.value)
    secretCopied.value = true
    setTimeout(() => {
      secretCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy secret:', error)
  }
}

// Close all dialogs
const closeDialogs = () => {
  showCreateDialog.value = false
  showEditDialog.value = false
  createdKeySecret.value = null
  secretCopied.value = false
  currentApiKey.value = null
  formData.value = {
    name: '',
    description: '',
    scope: 'read_write',
    status: 'active',
    rate_limit: 1000,
    expires_in_days: null
  }
}

// Get status badge class
const getStatusClass = (status) => {
  const classes = {
    active: 'bg-positive-dimmest text-positive-highest',
    inactive: 'bg-higher text-dimmer',
    revoked: 'bg-negative-dimmest text-negative-highest'
  }
  return classes[status] || classes.inactive
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

onMounted(() => {
  loadApiKeys()
})
</script>

<style lang="scss" scoped>
.api-keys-container {
  @apply max-w-6xl mx-auto p-6 flex flex-col gap-6;
}

.header {
  @apply flex items-start justify-between gap-4;
}

.btn-primary {
  @apply px-4 py-2 bg-primary-higher text-white-default rounded-lg hover:bg-primary-default transition-colors flex items-center font-medium;
}

.btn-secondary {
  @apply px-4 py-2 bg-higher text-default rounded-lg hover:bg-highest transition-colors font-medium;
}

.btn-danger {
  @apply px-4 py-2 bg-negative-higher text-white-default rounded-lg hover:bg-negative-default transition-colors font-medium;
}

.btn-icon {
  @apply p-2 text-dimmer hover:text-default hover:bg-higher rounded-lg transition-colors;

  &.btn-danger {
    @apply hover:bg-negative-dimmest hover:text-negative-default;
  }
}

.loading-container {
  @apply flex flex-col gap-4;
}

.skeleton-card {
  @apply h-48 rounded-lg bg-higher;
  background: linear-gradient(-45deg, var(--background-higher) 40%, var(--background-default) 55%, var(--background-higher) 63%);
  background-size: 400% 100%;
  background-position: 100% 50%;
  animation: skeleton-animation 2s ease infinite;
}

@keyframes skeleton-animation {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.api-keys-list {
  @apply flex flex-col gap-4;
}

.api-key-card {
  @apply border border-default rounded-lg overflow-hidden bg-default;
}

.card-header {
  @apply flex items-start justify-between gap-4 p-4 border-b border-default;
}

.card-actions {
  @apply flex items-center gap-2;
}

.status-badge {
  @apply px-2 py-1 rounded text-xs font-medium;
}

.card-body {
  @apply p-4;
}

.info-grid {
  @apply grid grid-cols-2 md:grid-cols-3 gap-4;
}

.info-item {
  @apply flex flex-col gap-1;
}

.info-label {
  @apply text-xs text-dimmest uppercase font-medium;
}

.info-value {
  @apply text-sm text-default;
}

.empty-state {
  @apply flex flex-col items-center justify-center py-16 text-center;
}

/* Modal Styles */
.modal-overlay {
  @apply fixed inset-0 bg-overlay flex items-center justify-center p-4;
  z-index: 9998;
}

.modal-content {
  @apply bg-default rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto;

  &.modal-sm {
    @apply max-w-md;
  }
}

.modal-header {
  @apply flex items-center justify-between p-6 border-b border-default;
}

.modal-body {
  @apply p-6;
}

.form {
  @apply flex flex-col gap-4;
}

.form-group {
  @apply flex flex-col gap-2;
}

.form-label {
  @apply text-sm font-medium text-default;
}

.form-input {
  @apply px-3 py-2 border border-default rounded-lg transition-colors;

  &:focus {
    outline: none;
    border-color: var(--primary-default);
  }
}

.form-actions {
  @apply flex justify-end gap-3 mt-4;
}

.alert {
  @apply p-4 rounded-lg;

  &.alert-warning {
    @apply bg-warning-dimmest border border-default;
  }
}

.secret-container {
  @apply flex items-center gap-2 p-2 rounded;
  background-color: var(--background-dimmest);
}

.secret-code {
  @apply flex-1 text-sm font-mono break-all;
  color: var(--positive-default);
}

.btn-copy {
  @apply p-2 text-dimmer hover:text-default transition-colors;
}
</style>
