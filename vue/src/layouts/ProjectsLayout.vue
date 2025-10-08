<template>
  <div class="w-full h-full pt-5 flex flex-col">
    <div class="px-6 border-b flex-shrink-0">
      <!-- 标题部分 -->
      <div class="pb-4">
        <h1 class="text-2xl font-semibold">{{ $t('projects.title') }}</h1>
        <p class="text-dimmer mt-2">{{ $t('projects.description') }}</p>
      </div>
    </div>
    <!-- 下面的内容 -->
    <slot></slot>
  </div>
</template>

<script setup>
/**
 * @description: 项目列表布局
 * @file: ProjectsLayout.vue
 * @since: 2025-01-08
 **/
</script>

<style lang="scss" scoped>
</style>