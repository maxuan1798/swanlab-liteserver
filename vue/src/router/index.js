import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 项目列表路由
  {
    path: '/',
    name: 'projects',
    component: () => import('@swanlab-vue/views/projects/ProjectsView.vue')
  },
  // 项目路由
  {
    path: '/project/:projectId',
    name: 'project',
    redirect: { name: 'overview' },
    children: [
      {
        path: '',
        name: 'overview',
        component: () => import('@swanlab-vue/views/home/HomeView.vue')
      },
      {
        path: 'charts',
        name: 'charts',
        component: () => import('@swanlab-vue/views/charts/ChartsView.vue')
      },
      {
        path: 'experiment/:experimentId',
        name: 'experiment',
        component: () => import('@swanlab-vue/views/experiment/ExperimentView.vue'),
        redirect: { name: 'experiment_chart' },
        children: [
          {
            path: 'index',
            name: 'experiment_index',
            component: () => import('@swanlab-vue/views/experiment/pages/index/IndexPage.vue')
          },
          {
            path: 'chart',
            name: 'experiment_chart',
            component: () => import('@swanlab-vue/views/experiment/pages/chart/ChartPage.vue')
          },
          {
            path: 'log',
            name: 'experiment_log',
            component: () => import('@swanlab-vue/views/experiment/pages/log/LogPage.vue')
          },
          {
            path: 'env',
            name: 'experiment_env',
            component: () => import('@swanlab-vue/views/experiment/pages/environment/EnvironmentPage.vue'),
            redirect: { name: 'exp_env_index' },
            children: [
              {
                path: 'index',
                name: 'exp_env_index',
                component: () => import('@swanlab-vue/views/experiment/pages/environment/pages/EnvIndex.vue')
              },
              {
                path: 'hardware',
                name: 'exp_env_hardware',
                component: () => import('@swanlab-vue/views/experiment/pages/environment/pages/EnvHardware.vue')
              },
              {
                path: 'requirements',
                name: 'exp_env_dependencies',
                component: () => import('@swanlab-vue/views/experiment/pages/environment/pages/EnvRequirements.vue')
              }
            ]
          }
        ]
      }
    ]
  },
  // 兼容旧路由，重定向到项目列表
  {
    path: '/projects',
    redirect: '/'
  },
  {
    path: '/charts',
    redirect: (to) => {
      const projectId = localStorage.getItem('currentProjectId') || '1'
      return `/project/${projectId}/charts`
    }
  },
  {
    path: '/experiment/:experimentId',
    redirect: (to) => {
      const projectId = localStorage.getItem('currentProjectId') || '1'
      return `/project/${projectId}/experiment/${to.params.experimentId}`
    }
  },
  {
    path: '/help',
    name: 'help',
    component: () => import('@swanlab-vue/views/help/HelpView.vue')
  },
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@swanlab-vue/views/error/pages/NotFound.vue')
  },
  { path: '/:pathMatch(.*)*', redirect: '/404' }
]

const router = createRouter({
  history: createWebHistory(),
  base: '/',
  routes
})

export default router
