<template>
  <div class="timeline">
    <div v-if="previewMode" class="preview-banner">
      预览中 — 行程调整预览
    </div>
    <DaySection
      v-for="day in days"
      :key="day.day_number"
      :day="day"
      :expanded-id="expandedPoiId"
      :preview-mode="previewMode"
      :changes="dayChanges(day.day_number)"
      :highlight-poi-id="highlightPoiId"
      @toggle="toggleExpand"
      @action="(type, poi) => $emit('action', type, poi)"
      @poi-click="(poiId) => $emit('poiClick', poiId)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DaySection from './DaySection.vue'
import type { DayData, ChangeItem, POIVisitData } from '../types/itinerary'

const props = defineProps<{
  days: DayData[]
  previewMode?: boolean
  previewChanges?: ChangeItem[] | null
  highlightPoiId?: string | number | null
}>()

defineEmits<{
  action: [type: 'replace' | 'delete' | 'insert_before' | 'insert_after', poi: POIVisitData]
  poiClick: [poiId: string | number]
}>()

const expandedPoiId = ref<string | number | null>(null)

function toggleExpand(id: string | number) {
  expandedPoiId.value = expandedPoiId.value === id ? null : id
}

function dayChanges(dayNumber: number): ChangeItem[] {
  if (!props.previewChanges) return []
  return props.previewChanges.filter((c) => c.day_number === dayNumber)
}
</script>

<style scoped>
.timeline { padding: 16px 0; }

.preview-banner {
  background: var(--color-sand-light);
  color: var(--color-coral-dark);
  font-size: 13px;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 6px;
  margin-bottom: 16px;
  border: 1px solid var(--color-sand-dark);
  text-align: center;
}
</style>
