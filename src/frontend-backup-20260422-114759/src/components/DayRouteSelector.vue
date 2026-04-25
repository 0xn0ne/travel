<template>
  <div class="day-route-selector">
    <button
      v-for="day in days"
      :key="day.day_number"
      class="day-pill"
      :class="{ 'day-pill-active': selectedDay === day.day_number }"
      :style="getPillStyle(day.day_number)"
      @click="selectDay(day.day_number)"
    >
      第{{ day.day_number }}天
    </button>
  </div>
</template>

<script setup lang="ts">
import type { DayData } from '../types/itinerary'

const props = defineProps<{
  days: DayData[]
  selectedDay: number | null
}>()

const emit = defineEmits<{
  select: [dayNumber: number]
}>()

const DAY_COLOR_VARS: Record<number, string> = {
  1: 'var(--color-day-1)',
  2: 'var(--color-day-2)',
  3: 'var(--color-day-3)',
}

function getPillStyle(dayNumber: number) {
  const isActive = props.selectedDay === dayNumber
  const dayColor = DAY_COLOR_VARS[dayNumber] || DAY_COLOR_VARS[1]

  if (isActive) {
    return {
      background: `linear-gradient(135deg, ${dayColor} 0%, color-mix(in srgb, ${dayColor} 82%, white) 100%)`,
      color: 'white',
      borderColor: dayColor,
      boxShadow: '0 12px 24px rgba(167, 139, 250, 0.18)',
    }
  }
  return {
    backgroundColor: '#ffffff',
    color: '#6e7584',
    borderColor: '#e4e7ef',
  }
}

function selectDay(dayNumber: number) {
  emit('select', dayNumber)
}
</script>

<style scoped>
.day-route-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px;
}

.day-pill {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.day-pill:hover:not(.day-pill-active) {
  background: #faf7ff !important;
  border-color: #d9d0ee !important;
  color: #5f6675 !important;
}

.day-pill-active {
  transform: translateY(-1px);
}
</style>
