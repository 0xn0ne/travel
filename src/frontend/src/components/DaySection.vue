<template>
  <div class="day-block">
    <div class="day-header">第{{ day.day_number }}天 · {{ day.theme }}</div>
    <div
      v-for="(poi, idx) in day.pois"
      :key="poi.poi_id || idx"
      class="poi-row"
      :class="{ 'poi-highlighted': highlightPoiId === (poi.poi_id || idx) }"
      @click="$emit('poiClick', poi.poi_id || idx)"
    >
      <POINode
        :poi="poi"
        :expanded="expandedId === (poi.poi_id || idx)"
        :preview-mode="previewMode"
        :change-type="getChangeType(poi, idx)"
        :replaced-poi="getReplacedPoi(poi, idx)"
        @toggle.stop="$emit('toggle', poi.poi_id || idx)"
        @action="(type, p) => $emit('action', type, p)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import POINode from './POINode.vue'
import type { DayData, ChangeItem, POIVisitData } from '../types/itinerary'

const props = defineProps<{
  day: DayData
  expandedId: string | number | null
  previewMode?: boolean
  changes?: ChangeItem[]
  highlightPoiId?: string | number | null
}>()

defineEmits<{
  toggle: [id: string | number]
  action: [type: 'replace' | 'delete' | 'insert_before' | 'insert_after', poi: POIVisitData]
  poiClick: [poiId: string | number]
}>()

function findChange(poi: POIVisitData, idx: number): ChangeItem | undefined {
  if (!props.changes) return undefined
  return props.changes.find(
    (c) => c.day_number === props.day.day_number && (c.position === idx || c.new_poi?.poi_id === poi.poi_id)
  )
}

function getChangeType(poi: POIVisitData, idx: number): 'add' | 'replace' | 'delete' | null {
  const change = findChange(poi, idx)
  if (!change) return null
  return change.action
}

function getReplacedPoi(poi: POIVisitData, idx: number): POIVisitData | null {
  const change = findChange(poi, idx)
  if (!change || change.action !== 'replace') return null
  return change.old_poi
}
</script>

<style scoped>
.day-block { margin-bottom: 28px; }
.day-header {
  font-weight: 700;
  font-size: 15px;
  color: var(--color-ocean);
  margin-bottom: 14px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-warm-border);
}

.poi-row {
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.poi-highlighted {
  background: var(--color-sand-light);
  box-shadow: inset 3px 0 0 var(--color-ocean);
}
</style>
