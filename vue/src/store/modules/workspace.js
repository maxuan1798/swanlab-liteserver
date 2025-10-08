import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 工作空间 store，用于管理当前工作空间及其下的项目列表
export const useWorkspaceStore = defineStore('workspace', () => {
  /** state */
  // 当前工作空间名称
  const currentWorkspace = ref(localStorage.getItem('currentWorkspace') || 'default')
  // 当前工作空间下的所有项目列表
  const projects = ref([])
  // 当前选中的项目ID
  const currentProjectId = ref(null)

  /** getter */
  const projectList = computed(() => projects.value)
  const currentProject = computed(() => {
    return projects.value.find(p => p.id === currentProjectId.value)
  })

  /** action */
  /**
   * 设置当前工作空间
   * @param {string} workspace 工作空间名称
   */
  const setWorkspace = (workspace) => {
    currentWorkspace.value = workspace
    localStorage.setItem('currentWorkspace', workspace)
  }

  /**
   * 设置项目列表
   * @param {Array} projectList 项目列表
   */
  const setProjects = (projectList) => {
    projects.value = projectList
    // 如果当前没有选中的项目，或者选中的项目不在列表中，自动选中第一个
    if (!currentProjectId.value || !projectList.find(p => p.id === currentProjectId.value)) {
      if (projectList.length > 0) {
        setCurrentProject(projectList[0].id)
      }
    }
  }

  /**
   * 设置当前项目
   * @param {number} projectId 项目ID
   */
  const setCurrentProject = (projectId) => {
    currentProjectId.value = projectId
    localStorage.setItem('currentProjectId', projectId)
  }

  /**
   * 清空状态
   */
  const clear = () => {
    projects.value = []
    currentProjectId.value = null
  }

  return {
    currentWorkspace,
    projects,
    currentProjectId,
    projectList,
    currentProject,
    setWorkspace,
    setProjects,
    setCurrentProject,
    clear
  }
})