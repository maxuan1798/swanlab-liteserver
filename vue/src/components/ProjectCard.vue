<template>
  <div class="project-card" @click="handleClick">
    <div class="project-icon">
      <SLIcon icon="runs" class="w-8 h-8" />
    </div>
    <div class="project-info">
      <h3 class="project-name">{{ project.name }}</h3>
      <p class="project-description" v-if="project.description">
        {{ project.description }}
      </p>
      <div class="project-meta">
        <div class="meta-item">
          <SLIcon icon="experiment" class="w-4 h-4" />
          <span>{{ experimentCount }} {{ $t('projects.card.experiments') }}</span>
        </div>
        <div class="meta-item" v-if="project.update_time">
          <span>{{ formatTime(project.update_time) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @description: 项目卡片组件
 * @file: ProjectCard.vue
 * @since: 2025-01-08
 **/
import { computed } from 'vue'
import SLIcon from '@swanlab-vue/components/SLIcon.vue'
import { formatTime } from '@swanlab-vue/utils/time'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const experimentCount = computed(() => {
  return props.project.experiment_count || 0
})

const handleClick = () => {
  emit('click', props.project)
}
</script>

<style lang="scss" scoped>
.project-card {
  @apply border rounded-lg p-6 bg-default hover:bg-higher cursor-pointer transition-all duration-200;
  @apply flex flex-col gap-4;

  &:hover {
    @apply shadow-lg border-primary-default;
  }
}

.project-icon {
  @apply w-12 h-12 rounded-lg bg-primary-dimmest flex items-center justify-center;
  @apply text-primary-default;
}

.project-info {
  @apply flex flex-col gap-2;
}

.project-name {
  @apply text-lg font-semibold truncate;
}

.project-description {
  @apply text-sm text-dimmer line-clamp-2;
  min-height: 2.5rem;
}

.project-meta {
  @apply flex items-center gap-4 text-xs text-dimmest mt-2;
}

.meta-item {
  @apply flex items-center gap-1;
}
</style>
