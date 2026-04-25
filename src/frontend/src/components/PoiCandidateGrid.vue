<template>
  <div class="candidate-grid">
    <PoiCandidateCard
      v-for="poi in pois"
      :key="poi.id"
      :poi="poi"
      :selected="selectedIds.includes(poi.id)"
      @toggle="$emit('toggle', poi.id)"
      @detail="$emit('detail', poi)"
    />
  </div>
</template>

<script setup lang="ts">
import PoiCandidateCard from './PoiCandidateCard.vue'
import type { CandidatePoiData } from '../types/itinerary'

defineProps<{
  pois: CandidatePoiData[]
  selectedIds: string[]
}>()

defineEmits<{
  toggle: [id: string]
  detail: [poi: CandidatePoiData]
}>()
</script>

<style scoped>
.candidate-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 18px;
}
@media (max-width: 1400px) {
  .candidate-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (max-width: 1120px) {
  .candidate-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 820px) {
  .candidate-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .candidate-grid { grid-template-columns: 1fr; }
}
</style>
