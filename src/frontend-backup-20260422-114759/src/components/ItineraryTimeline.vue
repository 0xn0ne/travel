<template>
  <div class="timeline-list">
    <DaySection
      v-for="day in days"
      :key="day.day_number"
      :day="day"
      :preview-mode="previewMode"
      :highlight-poi-id="highlightPoiId"
      @update-day="emit('update-day', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DaySection from './DaySection.vue'
import type { DayData } from '../types/itinerary'

const { days, previewMode, highlightPoiId } = defineProps<{
  days: DayData[]
  previewMode?: boolean
  highlightPoiId?: string | number | null
}>()

const emit = defineEmits<{
  'update-day': [day: DayData]
}>()

const addDialogVisible = ref(false)
void addDialogVisible

function openAddDialog() {
  addDialogVisible.value = true
}

defineExpose({ openAddDialog })
</script>

<style scoped>
.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
