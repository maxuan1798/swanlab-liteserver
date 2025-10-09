<template>
  <MainLayout :show-side-bar="!errorCode && !isProjectsPage" v-if="ready">
    <router-view v-if="!errorCode" />
    <ErrorView :code="errorCode" :message="errorMessage" v-else />
  </MainLayout>
  <!-- 全局气泡提示 -->
  <SLMessages ref="messagesRef" />
  <!-- 全局确认弹窗 -->
  <SLConfirm ref="confirmRef" />
</template>

<script setup>
import MainLayout from './layouts/main/MainLayout.vue'
import ErrorView from './views/error/ErrorView.vue'
import http from './api/http'
import { useProjectStore, useWorkspaceStore } from '@swanlab-vue/store'
import { computed } from 'vue'
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { watch } from 'vue'
import { installMessage, SLMessages, message } from '@swanlab-vue/components/message'
import { installConfirm, SLConfirm } from './components/confirm'
import { onMounted } from 'vue'

// ---------------------------------- state ----------------------------------

const projectStore = useProjectStore()
const workspaceStore = useWorkspaceStore()
const ready = ref()

// ---------------------------------- 在此处请求工作空间下的项目列表 ----------------------------------
const loadProjects = async () => {
  try {
    // 获取当前工作空间下的所有项目
    const { data } = await http.get(`/cloud/workspaces/${workspaceStore.currentWorkspace}/projects`)

    if (data && data.projects && data.projects.length > 0) {
      // 设置项目列表到 workspace store
      workspaceStore.setProjects(data.projects)

      // 如果有保存的 currentProjectId，尝试加载该项目
      const savedProjectId = localStorage.getItem('currentProjectId')
      const projectToLoad = savedProjectId ? data.projects.find((p) => p.id == savedProjectId) : data.projects[0]

      if (projectToLoad) {
        // 加载选中的项目详情
        const projectDetail = await http.get(`/project?project_id=${projectToLoad.id}`)
        projectStore.setProject(projectDetail.data)
        workspaceStore.setCurrentProject(projectToLoad.id)
      }
    } else {
      errorCode.value = 404 // 没有找到项目
    }
  } catch (error) {
    console.error('Failed to load projects:', error)
    errorCode.value = error.response?.data?.code || 3000
  } finally {
    ready.value = true
  }
}

loadProjects()

// ---------------------------------- 错误处理 ----------------------------------

const errorCode = ref(0) // 错误码
const errorMessage = ref('') // 错误信息
const route = useRoute()

// 判断是否在项目列表页面，如果是则不显示侧边栏
const isProjectsPage = computed(() => route.name === 'projects')

// 监测路由修改
watch(
  computed(() => route.fullPath),
  (oldVal) => {
    // console.log('route change', newVal, oldVal)
    if (oldVal === undefined) return
    // 清除消息弹窗
    message.clear()
  }
)

// ---------------------------------- 项目配置 ----------------------------------

const messagesRef = ref(null)
const confirmRef = ref(null)

onMounted(() => {
  // 注册全局顶部提醒
  installMessage(messagesRef)
  installConfirm(confirmRef)
})
</script>

<style scoped></style>
