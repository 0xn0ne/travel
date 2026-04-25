<template>
  <article class="candidate-card" :class="{ selected }" @click="$emit('detail')">
    <div class="card-image-wrap">
      <img v-if="poi.cover_image_url" :src="poi.cover_image_url" :alt="poi.name" class="card-image" />
      <div v-else class="card-image placeholder">{{ poi.name.slice(0, 1) }}</div>
      <div class="card-overlay"></div>
      <h3 class="card-title">{{ poi.name }}</h3>
      <button class="select-toggle" :class="{ active: selected }" type="button" @click.stop="$emit('toggle')">
        {{ selected ? '已选' : '选择' }}
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { CandidatePoiData } from '../types/itinerary'

defineProps<{
  poi: CandidatePoiData
  selected: boolean
}>()

defineEmits<{
  toggle: []
  detail: []
}>()
</script>

<style scoped>
.candidate-card {
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid #e4e7ef;
  background: rgba(255, 255, 255, 0.94);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  cursor: pointer;
}

.candidate-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(35, 38, 47, 0.08);
}

.candidate-card.selected {
  border-color: #a78bfa;
  box-shadow: 0 14px 30px rgba(167, 139, 250, 0.18);
}

.card-image-wrap {
  position: relative;
  aspect-ratio: 1;
  background: linear-gradient(180deg, #f6f1ff 0%, #efe9fb 100%);
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: #81879a;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(24, 28, 38, 0.06) 0%, rgba(24, 28, 38, 0.12) 45%, rgba(24, 28, 38, 0.72) 100%);
}

.card-title {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 14px;
  margin: 0;
  font-size: 15px;
  line-height: 1.35;
  color: #fff;
  font-weight: 800;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.28);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.select-toggle {
  position: absolute;
  top: 12px;
  right: 12px;
  min-width: 56px;
  height: 30px;
  padding: 0 10px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #4e5564;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s ease;
}

.select-toggle.active {
  background: linear-gradient(135deg, #a78bfa 0%, #8f79db 100%);
  border-color: transparent;
  color: #fff;
}

.select-toggle:hover {
  transform: translateY(-1px);
}
</style>
