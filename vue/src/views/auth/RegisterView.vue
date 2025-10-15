<template>
  <div class="auth-container">
    <!-- Tech Background Elements -->
    <div class="tech-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="infinity-grid"></div>
      <div class="wave-layer wave-1"></div>
      <div class="wave-layer wave-2"></div>
      <div class="particle-system">
        <div v-for="i in 20" :key="i" class="particle" :style="getParticleStyle(i)"></div>
      </div>
    </div>

    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">Sign Up</h1>
        <p class="auth-subtitle">Create your SwanLab account</p>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="name" class="form-label">Full Name</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            class="form-input"
            :class="{ 'form-input-error': errors.name }"
            placeholder="Enter your full name"
            required
          />
          <div v-if="errors.name" class="form-error">{{ errors.name }}</div>
        </div>

        <div class="form-group">
          <label for="email" class="form-label">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="form-input"
            :class="{ 'form-input-error': errors.email }"
            placeholder="Enter your email"
            required
          />
          <div v-if="errors.email" class="form-error">{{ errors.email }}</div>
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="form-input"
            :class="{ 'form-input-error': errors.password }"
            placeholder="Create a password"
            required
          />
          <div v-if="errors.password" class="form-error">{{ errors.password }}</div>
        </div>

        <div class="form-group">
          <label for="confirmPassword" class="form-label">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            class="form-input"
            :class="{ 'form-input-error': errors.confirmPassword }"
            placeholder="Confirm your password"
            required
          />
          <div v-if="errors.confirmPassword" class="form-error">{{ errors.confirmPassword }}</div>
        </div>

        <div v-if="authStore.error" class="form-error-message">
          {{ authStore.error }}
        </div>

        <button
          type="submit"
          class="auth-button"
          :disabled="authStore.isLoading"
        >
          <span v-if="authStore.isLoading">Creating Account...</span>
          <span v-else>Create Account</span>
        </button>
      </form>

      <div class="auth-footer">
        <p class="auth-link-text">
          Already have an account?
          <a href="#" class="auth-link" @click.prevent="$emit('switch-to-login')">Sign In</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@swanlab-vue/store'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateForm = () => {
  let isValid = true

  // Clear previous errors
  Object.keys(errors).forEach(key => {
    errors[key] = ''
  })

  // Name validation
  if (!form.name) {
    errors.name = 'Name is required'
    isValid = false
  } else if (form.name.length < 2) {
    errors.name = 'Name must be at least 2 characters'
    isValid = false
  }

  // Email validation
  if (!form.email) {
    errors.email = 'Email is required'
    isValid = false
  } else if (!/\S+@\S+\.\S+/.test(form.email)) {
    errors.email = 'Email is invalid'
    isValid = false
  }

  // Password validation
  if (!form.password) {
    errors.password = 'Password is required'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = 'Password must be at least 6 characters'
    isValid = false
  }

  // Confirm password validation
  if (!form.confirmPassword) {
    errors.confirmPassword = 'Please confirm your password'
    isValid = false
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
    isValid = false
  }

  return isValid
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  try {
    await authStore.register(form.email, form.password, form.name)

    // Redirect to home page after successful registration
    router.push('/')
  } catch (error) {
    // Error is already handled in the store
    console.error('Registration failed:', error)
  }
}

// Particle system for infinity concept
const getParticleStyle = (index) => {
  const size = Math.random() * 4 + 1
  const duration = Math.random() * 20 + 10
  const delay = Math.random() * 20
  const x = Math.random() * 100
  const y = Math.random() * 100

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${x}%`,
    top: `${y}%`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`,
    opacity: Math.random() * 0.3 + 0.1
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--background-default) 0%, var(--background-higher) 50%, var(--primary-dimmest) 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* Tech Background Elements */
.tech-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.6;
  animation: float 8s ease-in-out infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, var(--primary-dimmer) 0%, transparent 70%);
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--positive-dimmer) 0%, transparent 70%);
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.orb-3 {
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, var(--warning-dimmer) 0%, transparent 70%);
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

/* Infinity Grid Pattern */
.infinity-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(28, 116, 221, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(28, 116, 221, 0.02) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
  animation: gridScroll 40s linear infinite;
}

/* Wave Layers */
.wave-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--primary-dimmer) 20%,
    var(--positive-dimmer) 50%,
    var(--primary-dimmer) 80%,
    transparent 100%
  );
  mask-image: linear-gradient(90deg, transparent, black 20%, black 80%, transparent);
  -webkit-mask-image: linear-gradient(90deg, transparent, black 20%, black 80%, transparent);
}

.wave-1 {
  animation: waveMove 25s ease-in-out infinite;
  transform: translateY(20px);
}

.wave-2 {
  animation: waveMove 35s ease-in-out infinite reverse;
  opacity: 0.05;
  transform: translateY(-10px);
}

/* Particle System */
.particle-system {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  background: var(--primary-dimmer);
  border-radius: 50%;
  animation: particleFloat infinite linear;
}

@keyframes gridScroll {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(40px, 40px);
  }
}

@keyframes waveMove {
  0%, 100% {
    transform: translateX(-10%) scaleY(1);
  }
  25% {
    transform: translateX(10%) scaleY(1.2);
  }
  50% {
    transform: translateX(30%) scaleY(1);
  }
  75% {
    transform: translateX(10%) scaleY(0.8);
  }
}

@keyframes particleFloat {
  0% {
    transform: translateY(100vh) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px) rotate(360deg);
    opacity: 0;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.05);
  }
}

.auth-card {
  background: var(--background-paper);
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 420px;
  border: 1px solid var(--outline-dimmer);
  position: relative;
  z-index: 10;
  backdrop-filter: blur(10px);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.auth-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

.auth-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--outline-default);
  border-radius: 8px;
  font-size: 16px;
  background: var(--background-default);
  color: var(--text-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-default);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input-error {
  border-color: var(--error-default);
}

.form-error {
  font-size: 14px;
  color: var(--error-default);
  margin-top: 4px;
}

.form-error-message {
  background: var(--error-container);
  color: var(--error-default);
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  border: 1px solid var(--error-default);
}

.auth-button {
  width: 100%;
  padding: 12px 16px;
  background: var(--primary-default);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.auth-button:hover:not(:disabled) {
  background: var(--primary-hover);
}

.auth-button:disabled {
  background: var(--outline-default);
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
}

.auth-link-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.auth-link {
  color: var(--primary-default);
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.auth-link:hover {
  text-decoration: underline;
}
</style>