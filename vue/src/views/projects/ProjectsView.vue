<template>
  <ProjectsLayout>
    <div class="projects-container">
      <!-- 加载中状态 -->
      <div v-if="loading" class="loading-container">
        <div v-for="i in 6" :key="i" class="skeleton-card"></div>
      </div>

      <!-- 项目列表 -->
      <div v-else-if="projects.length > 0" class="projects-grid">
        <ProjectCard v-for="project in projects" :key="project.id" :project="project" @click="navigateToProject" />
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <SLIcon icon="runs" class="w-16 h-16 text-dimmest" />
        <p class="text-dimmer text-lg mt-4">{{ $t('projects.empty.title') }}</p>
        <p class="text-dimmest text-sm mt-2">{{ $t('projects.empty.description') }}</p>
      </div>
    </div>
  </ProjectsLayout>
</template>

<script setup>
/**
 * @description: 项目列表视图
 * @file: ProjectsView.vue
 * @since: 2025-01-08
 **/
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore, useProjectStore } from '@swanlab-vue/store'
import ProjectsLayout from '@swanlab-vue/layouts/ProjectsLayout.vue'
import ProjectCard from '@swanlab-vue/components/ProjectCard.vue'
import SLIcon from '@swanlab-vue/components/SLIcon.vue'
import http from '@swanlab-vue/api/http'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const projectStore = useProjectStore()

const loading = ref(true)
const projects = computed(() => workspaceStore.projects || [])

// 导航到具体项目
const navigateToProject = async (project) => {
  try {
    // 设置当前项目
    workspaceStore.setCurrentProject(project.id)

    // 加载项目详细信息
    const { data } = await http.get(`/project?project_id=${project.id}`)
    projectStore.setProject(data)

    // 跳转到项目页面
    router.push(`/project/${project.id}`)
  } catch (error) {
    console.error('Failed to navigate to project:', error)
  }
}

// 页面加载时确保项目列表已加载
onMounted(async () => {
  if (!projects.value || projects.value.length === 0) {
    try {
      const { data } = await http.get(`/cloud/workspaces/${workspaceStore.currentWorkspace}/projects`)
      if (data && data.projects) {
        workspaceStore.setProjects(data.projects)
      }
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }
  loading.value = false
})
</script>

<style lang="scss" scoped>
.projects-container {
  @apply p-6 flex-grow overflow-auto;
}

.projects-grid {
  @apply grid gap-6;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.loading-container {
  @apply grid gap-6;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.skeleton-card {
  @apply h-48 rounded-lg;
  background: linear-gradient(-45deg, #f5f5f5 40%, #fff 55%, #f5f5f5 63%);
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

.empty-state {
  @apply flex flex-col items-center justify-center pt-20;
}
</style>
