<template>
  <article class="candidate-card" :class="{ selected }" @click="$emit('detail')">
    <div class="card-image-wrap">
      <div class="sticker-pin"></div>
      <img v-if="poi.cover_image_url" :src="poi.cover_image_url" :alt="poi.name" class="card-image" />
      <div v-else class="card-image placeholder">
        <span class="placeholder-icon">🐾</span>
        <span class="placeholder-letter">{{ poi.name.slice(0, 1) }}</span>
      </div>
      <div class="card-overlay"></div>
      <div class="card-badge">{{ poi.district || '旅行贴纸' }}</div>
      <h3 class="card-title">{{ poi.name }}</h3>
      <button class="select-toggle" :class="{ active: selected }" type="button" @click.stop="$emit('toggle')">
        {{ selected ? '已贴上' : '贴上它' }}
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
  border-radius: 28px;
  border: 2px solid #1f1f1f;
  background: linear-gradient(180deg, #fffefd 0%, #f6f7ff 100%);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(108, 124, 240, 0.12);
}

.candidate-card:hover {
  transform: translateY(-4px) rotate(-0.6deg);
  box-shadow: 0 18px 30px rgba(108, 124, 240, 0.16);
}

.candidate-card.selected {
  border-color: #6c7cf0;
  box-shadow: 0 20px 34px rgba(108, 124, 240, 0.22);
}

.card-image-wrap {
  position: relative;
  aspect-ratio: 1;
  background: linear-gradient(180deg, #f7f4ef 0%, #eef1ff 100%);
}

.sticker-pin {
  position: absolute;
  top: 12px;
  left: 14px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #ffffff 0%, #f7c8a0 58%, #e79f6f 100%);
  border: 2px solid #1f1f1f;
  z-index: 3;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #4d4d4d;
  background: linear-gradient(180deg, #f7f4ef 0%, #eef1ff 100%);
}

.placeholder-icon {
  font-size: 34px;
}

.placeholder-letter {
  font-size: 36px;
  font-weight: 900;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(31, 31, 31, 0.04) 0%, rgba(31, 31, 31, 0.16) 42%, rgba(31, 31, 31, 0.7) 100%);
}

.card-badge {
  position: absolute;
  left: 14px;
  top: 14px;
  padding: 7px 11px 7px 36px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.95);
  color: #2f2f2f;
  font-size: 11px;
  font-weight: 900;
  border: 2px solid #1f1f1f;
  z-index: 2;
}

.card-title {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 18px;
  margin: 0;
  font-size: 16px;
  line-height: 1.4;
  color: #fff;
  font-weight: 900;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.24);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.select-toggle {
  position: absolute;
  top: 14px;
  right: 14px;
  min-width: 74px;
  height: 34px;
  padding: 0 12px;
  border: 2px solid #1f1f1f;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: #2f2f2f;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.18s ease;
  z-index: 2;
}

.select-toggle.active {
  background: #6c7cf0;
  border-color: #1f1f1f;
  color: #fff;
  box-shadow: 0 10px 18px rgba(108, 124, 240, 0.2);
}

.select-toggle:hover {
  transform: translateY(-1px) scale(1.02);
}
</style>
