<template>
  <div class="w-full h-full bg-dimmest text-dimmest flex justify-between items-center px-6">
    <!-- logo, version and workspace selector -->
    <div class="flex items-center gap-6">
      <!-- logo and version -->
      <div class="flex items-center gap-1.5 hover:cursor-pointer" @click="goHome">
        <!-- icon -->
        <HeaderIcon />
        <!-- version -->
        <div class="flex items-end">
          <span class="font-semibold mr-0.5">SwanLab</span>
          <!-- 版本号被注释了 -->
          <!-- <span class="whitespace-nowrap text-xs pl-2 text-dimmer"> {{ formatVersion(version) }}</span> -->
        </div>
      </div>
      <!-- workspace selector -->
      <div class="flex items-center gap-2">
        <span class="text-sm text-dimmer">Workspace:</span>
        <SLMenu class="w-48" down>
          <template #default="{ open }">
            <div class="px-3 py-1.5 border rounded hover:border-primary-default cursor-pointer">
              <span class="text-sm">{{ workspaceStore.currentWorkspace }}</span>
            </div>
          </template>
          <template #pop="{ close }">
            <SLMenuItem
              v-for="workspace in workspaces"
              :key="workspace.name"
              @click="selectWorkspace(workspace.name, close)"
            >
              <div class="flex justify-between items-center w-full">
                <span class="text-sm">{{ workspace.name }}</span>
                <span class="text-xs text-dimmer ml-2">({{ workspace.project_count }})</span>
              </div>
            </SLMenuItem>
            <!-- 如果没有 workspace，显示默认值 -->
            <div v-if="workspaces.length === 0" class="px-3 py-2 text-sm text-dimmer">No workspaces</div>
          </template>
        </SLMenu>
      </div>
    </div>
    <div class="w-full grow flex justify-end gap-6 pl-8 pr-4">
      <!-- links -->
      <div class="pl-6 items-center font-semibold gap-6 md:flex hidden">
        <a
          :href="item.link"
          target="_blank"
          class="w-16 hover:text-white-higher text-center"
          v-for="item in links"
          :key="item.link"
        >
          {{ item.title }}
        </a>
      </div>
    </div>
    <!-- fixeds -->
    <div class="flex items-center font-semibold gap-6">
      <!-- User profile dropdown -->
      <div v-if="authStore.isAuthenticated" class="flex items-center">
        <SLMenu class="w-48" down>
          <template #default="{ open }">
            <div class="flex items-center gap-2 px-3 py-1.5 border rounded hover:border-primary-default cursor-pointer">
              <div class="w-6 h-6 rounded-full bg-primary-default flex items-center justify-center text-white text-xs font-semibold">
                {{ authStore.currentUser?.name?.charAt(0)?.toUpperCase() || 'U' }}
              </div>
              <span class="text-sm">{{ authStore.currentUser?.name }}</span>
            </div>
          </template>
          <template #pop="{ close }">
            <SLMenuItem @click="handleProfile(close)">
              <div class="flex items-center gap-2 w-full">
                <SLIcon icon="user" class="w-4 h-4" />
                <span class="text-sm">Profile</span>
              </div>
            </SLMenuItem>
            <SLMenuItem @click="handleLogout(close)">
              <div class="flex items-center gap-2 w-full text-error-default">
                <SLIcon icon="logout" class="w-4 h-4" />
                <span class="text-sm">Logout</span>
              </div>
            </SLMenuItem>
          </template>
        </SLMenu>
      </div>

      <!-- button: language switch -->
      <div class="flex items-center font-semibold">
        <button @click="switchLang()" class="switchLang relative w-9 h-9">
          <div :class="mainLangClass">中</div>
          <div :class="secondLangClass">En</div>
        </button>
      </div>
      <a
        :href="item.link"
        target="_blank"
        class="flex gap-1.5 items-center h-full text-dimmest hover:text-white-higher"
        v-for="item in fixeds"
        :key="item.icon"
      >
        <SLIcon :icon="item.icon" class="h-8 w-8" />
        <!-- {{ item.title }} -->
      </a>
    </div>
  </div>
</template>

<script setup>
/**
 * @description: 顶部页头
 * @file: PageHeader.vue
 * @since: 2024-01-09 11:13:20
 **/

import { ref, computed } from 'vue'
import HeaderIcon from './HeaderIcon.vue'
import SLIcon from '@swanlab-vue/components/SLIcon.vue'
import SLMenu from '@swanlab-vue/components/menu/SLMenu.vue'
import SLMenuItem from '@swanlab-vue/components/menu/SLMenuItem.vue'
import { getDefaultLang } from '@swanlab-vue/i18n'
import { useI18n } from 'vue-i18n'
import { t } from '@swanlab-vue/i18n'
import { useWorkspaceStore, useAuthStore } from '@swanlab-vue/store'
import { useRouter } from 'vue-router'
import http from '@swanlab-vue/api/http'

const router = useRouter()

defineProps({
  version: {
    type: String,
    default: 'unknown'
  }
})

// ---------------------------------- 格式化版本号 ----------------------------------
// const formatVersion = (version) => {
//   if (version === 'unknown') return version
//   return 'v' + version
// }

// ---------------------------------- 链接配置 ----------------------------------

// *静态数据 国际化需要放到computed中，切换时才会有响应式
const links = computed(() => [
  {
    title: t('nav.docs'),
    link: 'https://docs.swanlab.cn/zh/guide_cloud/general/what-is-swanlab.html'
  },
  {
    title: t('nav.examples'),
    link: 'https://docs.swanlab.cn/zh/examples/mnist.html'
  },
  {
    title: t('nav.feedback'),
    link: 'https://github.com/SwanHubX/SwanLab/issues'
  }
])

const fixeds = ref([
  {
    title: 'GitHub',
    icon: 'github',
    link: 'https://github.com/SwanHubX/SwanLab'
  }
])

// ---------------------------------- 跳转到首页 ----------------------------------
const goHome = () => {
  router.push('/')
}

// ---------------------------------- Authentication ----------------------------------
const authStore = useAuthStore()

// ---------------------------------- workspace 选择 ----------------------------------
const workspaceStore = useWorkspaceStore()
const workspaces = ref([])

// 加载 workspace 列表
const loadWorkspaces = async () => {
  try {
    const { data } = await http.get('/cloud/workspaces')
    if (data && data.workspaces) {
      workspaces.value = data.workspaces
    }
  } catch (error) {
    console.error('Failed to load workspaces:', error)
    // 如果加载失败，使用默认值
    workspaces.value = [{ name: 'default', project_count: 0 }]
  }
}

// 页面加载时获取 workspace 列表
loadWorkspaces()

const selectWorkspace = async (workspace, close) => {
  workspaceStore.setWorkspace(workspace)
  close()
  // 触发重新加载 projects
  window.location.reload()
}

// ---------------------------------- 切换语言 ----------------------------------
const nowLangKey = ref(getDefaultLang())
const { locale } = useI18n()

const [mainLangInit, secondLangInit] =
  locale.value === 'zh-CN' ? ['mainlang', 'secondlang'] : ['secondlang', 'mainlang']
const mainLangClass = ref(mainLangInit)
const secondLangClass = ref(secondLangInit)

const switchLang = () => {
  locale.value = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  const lang = locale.value
  document.documentElement.lang = lang.toLowerCase()
  localStorage.setItem('lang', lang)

  //图标样式切换
  const temp = mainLangClass.value
  mainLangClass.value = secondLangClass.value
  secondLangClass.value = temp
}

// ---------------------------------- User Profile Handlers ----------------------------------
const handleProfile = (close) => {
  close()
  // TODO: Navigate to profile page when implemented
  console.log('Navigate to profile page')
}

const handleLogout = async (close) => {
  close()
  try {
    await authStore.logout()
    // Redirect to login page after logout
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}
</script>

<style lang="scss" scoped>
.a-hover {
  &:hover {
    @apply text-white-higher;
  }
}

.switchLang:hover .mainlang {
  @apply bg-white-higher;
}

.switchLang:hover .secondlang {
  @apply border-white-higher text-white-higher;
}

.mainlang {
  @apply absolute top-0 left-0 w-6 h-6 z-[1] rounded bg-white-highest text-default text-sm content-center duration-100 ease-in-out;
}

.secondlang {
  @apply absolute left-3 top-3 w-6 h-6 z-[0] rounded border-[1px] border-white-highest text-dimmest text-sm content-center duration-100 ease-in-out;
}
</style>
