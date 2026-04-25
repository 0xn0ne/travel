<template>
  <div class="day-block">
    <div class="day-header">
      <span>第{{ day.day_number }}天 · {{ day.theme }}</span>
    </div>

    <draggable
      v-model="localPois"
      item-key="id"
      ghost-class="poi-ghost"
      animation="200"
      group="itinerary-pois"
      @end="onDragEnd"
    >
      <template #item="{ element: poi, index }">
        <div class="poi-wrapper">
          <div
            class="poi-card"
            :class="{ 'poi-highlighted': highlightPoiId === poi.poi_id }"
            :data-poi-id="poi.poi_id"
          >
            <div class="poi-content">
              <span class="poi-time">{{ poi.time_slot }}</span>
              <span class="poi-name">{{ poi.name }}</span>
            </div>
            <button class="delete-btn" @click.stop="deletePoi(index)" title="删除">
              删除
            </button>
          </div>
        </div>
      </template>
    </draggable>

    <div v-if="localPois.length === 0" class="empty-day">
      <span>拖拽景点到此处</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import draggable from 'vuedraggable'
import type { DayData, POIVisitData } from '../types/itinerary'

interface DragPOI extends POIVisitData {
  id: string
}

const props = defineProps<{
  day: DayData
  previewMode?: boolean
  highlightPoiId?: string | number | null
}>()

const emit = defineEmits<{
  'update-day': [day: DayData]
}>()

const localPois = computed<DragPOI[]>({
  get: () => {
    return (props.day.pois || []).map((poi, index) => ({
      ...poi,
      id: `${props.day.day_number}-${poi.poi_id || index}-${Date.now()}-${Math.random()}`
    }))
  },
  set: (newPois: DragPOI[]) => {
    const cleanPois = newPois.map(({ id, ...poi }) => poi as POIVisitData)
    emitUpdate(cleanPois)
  }
})

function deletePoi(index: number) {
  const newPois = [...(props.day.pois || [])]
  newPois.splice(index, 1)
  emitUpdate(newPois)
}

function onDragEnd() {
}

function emitUpdate(newPois: POIVisitData[]) {
  const updatedDay = {
    ...props.day,
    pois: newPois
  }
  emit('update-day', updatedDay)
}
</script>

<style scoped>
.day-block {
  padding: 18px;
  border: 1px solid #DCE4F5;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(250, 248, 255, 0.92) 0%, rgba(255, 255, 255, 0.96) 100%);
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 800;
  font-size: 16px;
  color: #FF9F6B;
  margin-bottom: 14px;
}

.poi-wrapper {
  margin-bottom: 10px;
}

.poi-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #DCE4F5;
  border-radius: 18px;
  box-shadow: 0 8px 20px rgba(35, 38, 47, 0.04);
  cursor: grab;
  transition: all 0.18s ease;
}

.poi-card:hover {
  box-shadow: 0 14px 28px rgba(35, 38, 47, 0.08);
  border-color: #C5DEFF;
  transform: translateY(-1px);
}

.poi-card:active {
  cursor: grabbing;
}

.poi-highlighted {
  background: #EDF4FC;
  border-color: #6C8CD5;
  box-shadow: 0 14px 32px rgba(108, 140, 213, 0.14);
}

.poi-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.poi-time {
  font-size: 12px;
  color: #8a91a1;
  white-space: nowrap;
  flex-shrink: 0;
}

.poi-name {
  font-weight: 700;
  font-size: 14px;
  color: #2f3542;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-btn {
  min-width: 50px;
  height: 32px;
  border: 1px solid #DCE4F5;
  border-radius: 10px;
  background: #fff;
  color: #8d7388;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  opacity: 0;
  font-size: 12px;
  font-weight: 700;
}

.poi-wrapper:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #faf6ff;
  border-color: #C5DEFF;
  color: #FF9F6B;
}

.poi-ghost {
  opacity: 0.55;
  background: #EDF4FC;
}

.empty-day {
  padding: 22px;
  text-align: center;
  color: #8d93a2;
  font-size: 13px;
  background: #faf8fd;
  border-radius: 16px;
  border: 1px dashed #DCE4F5;
}
</style>
