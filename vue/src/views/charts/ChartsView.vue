<template>
  <div class="flex flex-col min-h-full bg-higher">
    <ChartsPage
      v-if="groups.length > 0"
      :groups="groups"
      :charts="charts"
      :default-color="defaultColor"
      :get-color="getColor"
      :key="chartsPageKey"
    />
    <!-- 图表不存在 -->
    <p class="font-semibold pt-5 text-center" v-else-if="ready">Empty Charts</p>
  </div>
</template>

<script setup>
/**
 * @description: 项目对比图表，本组件完成项目对比图表的数据的请求和展示，大致流程是：
 * 1. 通过 http.get('/project/charts') 请求项目对比图表的数据，渲染到页面上
 * 2. 根据每个图表的数据源
 * @file: ChartsView.vue
 * @since: 2024-01-27 13:05:27
 **/
import http from '@swanlab-vue/api/http'
import { useProjectStore, useWorkspaceStore } from '@swanlab-vue/store'
import { ref } from 'vue'
import ChartsPage from './components/ChartsPage.vue'
import { onUnmounted } from 'vue'
const projectStore = useProjectStore()
const workspaceStore = useWorkspaceStore()
http.get(`/project/${workspaceStore.currentProjectId}/charts`).then(({ data }) => {
  // 将namespaces转换为groups
  charts.value = data.charts
  namespaces.value = data.namespaces
  groups.value = generateGroups()
  ready.value = true
})
const ready = ref(false)
// ---------------------------------- 数据驱动 ----------------------------------
// 项目对比图表数据，[{name, charts: [charts]}]
const groups = ref([])
const charts = ref([])
const namespaces = ref([])
const chartsPageKey = ref(0)

const generateGroups = () => {
  // 生成groups
  const groups = []

  // 当后端未提供 namespaces 时，使用一个默认分组包含所有可见图表
  if (!namespaces.value || namespaces.value.length === 0) {
    const fallbackCharts = []
    charts.value.forEach((chart) => {
      if (!chart) return
      // 规范化字段：后端可能使用 key/chart_type
      const normalized = {
        ...chart,
        name: chart.name ?? chart.key,
        type: chart.type ?? chart.chart_type ?? 'line'
      }
      // 如果chart的所有source都为不可见，不加入
      const allSourcesInvisible = normalized.source?.every((source) => !projectStore.showMap[source])
      if (allSourcesInvisible) return
      // 仅保留未报错的 source
      const sources = normalized.source?.filter((source) => !(normalized.error && normalized.error[source])) || []
      const validSourcesInvisible = sources.every((source) => !projectStore.showMap[source])
      if (validSourcesInvisible) return
      fallbackCharts.push(normalized)
    })
    if (fallbackCharts.length) {
      groups.push({ name: 'Default', charts: fallbackCharts })
    }
    return groups
  }

  namespaces.value.forEach((namespace) => {
    const group = {
      ...namespace,
      charts: []
    }
    namespace.charts.forEach((chart_id) => {
      const chart = charts.value.find((chart) => {
        return chart.id === chart_id
      })
      if (!chart) {
        return
      }
      // 规范化字段
      const normalized = {
        ...chart,
        name: chart.name ?? chart.key,
        type: chart.type ?? chart.chart_type ?? 'line'
      }
      // 如果chart的所有source都为不可见，不push
      const allSourcesInvisible = normalized.source.every((source) => !projectStore.showMap[source])
      if (allSourcesInvisible) return

      // 首先找到所有source中不在error的keys中的source
      const sources = normalized.source.filter((source) => !normalized.error[source])

      const validSourcesInvisible = sources.every((source) => !projectStore.showMap[source])
      if (validSourcesInvisible) return

      // 如果在source中不在error的keys中的都不可见，不push
      group.charts.push(normalized)
    })
    // 如果group的所有chart都为不可见，不push
    if (group.charts.length) {
      groups.push(group)
    }
  })
  return groups
}

// ---------------------------------- 向projectStore注册回调，当点击眼睛时执行此回调 ----------------------------------
const handleShowChange = () => {
  // 重新渲染页面
  chartsPageKey.value++
  // 重新生成groups
  groups.value = generateGroups()
}
// 注册点击眼睛的回调
projectStore.registerChangeShowCallback(handleShowChange)

onUnmounted(() => {
  projectStore.destoryChangeShowCallback()
})

// ---------------------------------- 色盘注入 ----------------------------------
const getColor = (() => {
  // 遍历所有实验，实验名称为key，实验颜色为value
  const colors = projectStore.colorMap
  return (exp_name) => {
    return colors[exp_name]
  }
})()
const defaultColor = projectStore.colors[0]
</script>

<style lang="scss" scoped></style>
