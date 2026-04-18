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

// Day route colors as CSS variable names
const DAY_COLOR_VARS: Record<number, string> = {
  1: 'var(--color-day-1)',
  2: 'var(--color-day-2)',
  3: 'var(--color-day-3)',
}

// Active day pills use the day color, inactive use sand colors
function getPillStyle(dayNumber: number) {
  const isActive = props.selectedDay === dayNumber
  const dayColor = DAY_COLOR_VARS[dayNumber] || DAY_COLOR_VARS[1]
  
  if (isActive) {
    return {
      backgroundColor: dayColor,
      color: 'white',
      borderColor: dayColor,
    }
  } else {
    return {
      backgroundColor: 'var(--color-sand-light)',
      color: 'var(--color-warm-text-muted)',
      borderColor: 'var(--color-warm-border)',
    }
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
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-warm-bg);
  border-bottom: 1px solid var(--color-warm-border);
}

.day-pill {
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid;
  transition: var(--transition-smooth);
  white-space: nowrap;
}

.day-pill:hover:not(.day-pill-active) {
  background: var(--color-sand);
  color: var(--color-warm-text);
}

.day-pill-active {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}
</style>
