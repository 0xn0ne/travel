<template>
  <div class="diary-view">
    <div class="diary-cover">
      <div class="cover-kicker">旅行手帐</div>
      <div class="cover-title">{{ title || '旅行手帐' }}</div>
      <div class="cover-meta">
        <span class="cover-tag">{{ dateRange }}</span>
        <span class="cover-tag">{{ peopleCount }}</span>
        <span class="cover-tag" v-if="totalDistance">{{ totalDistance }}</span>
        <span class="cover-weather" v-if="weather">{{ weather }}</span>
      </div>
      <div class="cover-taste-tags" v-if="tasteTags && tasteTags.length">
        <span v-for="tag in tasteTags" :key="tag" class="taste-tag">{{ tag }}</span>
      </div>
    </div>

    <div
      v-for="day in days"
      :key="day.day_number"
      class="day-diary"
    >
      <div class="timeline-rail">
        <div class="timeline-dot" />
        <div class="timeline-line" />
      </div>

      <div class="day-content">
        <div class="day-header">
          <div class="day-title">
            {{ day.theme || `Day ${day.day_number}` }}
          </div>
          <div class="day-date" v-if="(day as any).date">{{ (day as any).date }}</div>
        </div>

        <div class="poi-list">
          <div
            v-for="(poi, idx) in day.pois"
            :key="idx"
            class="poi-card"
            :class="{ highlighted: highlightedId === poi.poi_id }"
            @click="handlePoiClick(poi)"
          >
            <div class="poi-emoji">{{ getPoiEmoji(poi) }}</div>

            <div class="poi-body">
              <div class="poi-time">{{ poi.time_slot }}</div>
              <div class="poi-name">{{ poi.name }}</div>
              <div class="poi-vibe" v-if="poi.vibe_description">{{ poi.vibe_description }}</div>
              <div class="poi-note" v-if="poi.highlight_note">
                <span class="note-icon">提示</span>
                {{ poi.highlight_note }}
              </div>
            </div>

            <div class="walk-to-next" v-if="poi.walk_to_next_minutes && idx < day.pois.length - 1">
              <div class="walk-line" />
              <span class="walk-text">步行 {{ poi.walk_to_next_minutes }} 分钟</span>
            </div>
          </div>
        </div>

        <div class="day-summary" v-if="(day as any).summary">
          {{ (day as any).summary }}
        </div>
      </div>
    </div>

    <div class="diary-footer">
      <span>用更舒服的节奏，记录这次出发。</span>
      <span class="footer-logo">拾途</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DayData, POIVisitData } from '../types/itinerary'

defineProps<{
  days: DayData[]
  title?: string
  dateRange?: string
  peopleCount?: string
  totalDistance?: string
  weather?: string
  tasteTags?: string[]
  highlightedId?: string | number | null
}>()

const emit = defineEmits<{
  poiClick: [poi: POIVisitData]
}>()

function handlePoiClick(poi: POIVisitData) {
  emit('poiClick', poi)
}

function getPoiEmoji(poi: POIVisitData): string {
  const name = poi.name || ''
  const vibe = poi.vibe_description || ''
  const text = (name + vibe).toLowerCase()

  if (text.includes('虹桥') || text.includes('站') || text.includes('机场')) return '🚄'
  if (text.includes('豫园') || text.includes('古') || text.includes('寺庙')) return '🏛️'
  if (text.includes('外滩') || text.includes('江') || text.includes('夜景')) return '🌆'
  if (text.includes('小笼') || text.includes('馒头') || text.includes('餐饮') || text.includes('午餐') || text.includes('晚餐')) return '🥟'
  if (text.includes('咖啡') || text.includes('cafe')) return '☕'
  if (text.includes('武康') || text.includes('路') || text.includes('思南')) return '🗺️'
  if (text.includes('新天地') || text.includes('iapm') || text.includes('购物')) return '🛍️'
  if (text.includes('西湖')) return '🌊'
  if (text.includes('博物馆')) return '🏛️'
  if (text.includes('公园')) return '🌿'
  if (text.includes('酒店') || text.includes('民宿')) return '🏨'
  if (text.includes('早餐') || text.includes('brunch')) return '🍳'
  if (text.includes('返程')) return '🚄'

  return '📍'
}
</script>

<style scoped>
.diary-view {
  min-height: 60vh;
}

.diary-cover {
  background: linear-gradient(135deg, #7BA8E0 0%, #6C8CD5 52%, #DCE9FF 100%);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 24px;
  padding: 24px 22px 20px;
  color: white;
  position: relative;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: 0 18px 34px rgba(108, 140, 213, 0.16);
}

.diary-cover::before {
  content: '';
  position: absolute;
  top: -28px;
  right: -24px;
  width: 140px;
  height: 140px;
  background: rgba(255,255,255,0.12);
  border-radius: 50%;
}

.cover-kicker {
  position: relative;
  z-index: 1;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.82);
  margin-bottom: 8px;
}

.cover-title {
  font-size: 28px;
  font-weight: 800;
  color: white;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
  line-height: 1.2;
}

.cover-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  position: relative;
  z-index: 1;
}

.cover-tag,
.cover-weather,
.taste-tag {
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 999px;
  color: white;
  background: rgba(255,255,255,0.16);
  border: 1px solid rgba(255,255,255,0.22);
}

.cover-taste-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 12px;
  position: relative;
  z-index: 1;
}

.day-diary {
  display: flex;
  gap: 0;
  position: relative;
  background: rgba(255,255,255,0.92);
  border: 1px solid #DCE4F5;
  border-radius: 22px;
  margin-bottom: 12px;
  box-shadow: 0 14px 30px rgba(35, 38, 47, 0.05);
}

.timeline-rail {
  width: 40px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 26px;
  position: relative;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #6C8CD5;
  box-shadow: 0 0 0 6px rgba(108, 140, 213, 0.12);
  z-index: 1;
  flex-shrink: 0;
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(to bottom, #DCE9FF, rgba(108, 140, 213, 0.08));
  margin-top: 8px;
  min-height: 52px;
}

.day-content {
  flex: 1;
  padding: 22px 18px 18px 0;
}

.day-header {
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0ecf7;
}

.day-title {
  font-size: 20px;
  font-weight: 800;
  color: #FF9F6B;
  margin-bottom: 3px;
}

.day-date {
  font-size: 12px;
  color: #9aa1af;
}

.poi-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.poi-card {
  display: flex;
  gap: 0;
  position: relative;
  background: #fff;
  border: 1px solid #DCE4F5;
  border-radius: 18px;
  padding: 14px 14px 12px;
  box-shadow: 0 8px 20px rgba(35,38,47,0.04);
  transition: all 0.18s ease;
  cursor: pointer;
}

.poi-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(35,38,47,0.08);
  border-color: #d9d0ee;
}

.poi-card.highlighted {
  border-color: #C5DEFF;
  box-shadow: 0 16px 30px rgba(108, 140, 213, 0.14);
  background: #EDF4FC;
}

.poi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #DCE4F5, #6C8CD5, #EDF4FC);
  border-radius: 18px 18px 0 0;
}

.poi-emoji {
  width: 38px;
  height: 38px;
  background: #EDF4FC;
  border: 1px solid #DCE4F5;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  margin-right: 12px;
  margin-top: 2px;
}

.poi-body {
  flex: 1;
  min-width: 0;
}

.poi-time {
  font-size: 11px;
  color: #FF9F6B;
  font-weight: 700;
  margin-bottom: 4px;
  letter-spacing: 0.03em;
}

.poi-name {
  font-size: 15px;
  font-weight: 800;
  color: #2f3542;
  margin-bottom: 4px;
  line-height: 1.35;
}

.poi-vibe {
  font-size: 12px;
  color: #8a90a0;
  line-height: 1.6;
  margin-bottom: 8px;
}

.poi-note {
  display: inline-flex;
  align-items: flex-start;
  gap: 6px;
  background: #EDF4FC;
  border: 1px solid #C5DEFF;
  border-radius: 10px;
  padding: 7px 10px;
  font-size: 12px;
  color: #6a6480;
  line-height: 1.5;
}

.note-icon {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6C8CD5;
  flex-shrink: 0;
  margin-top: 2px;
}

.walk-to-next {
  position: absolute;
  bottom: -14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
}

.walk-line {
  width: 1px;
  height: 10px;
  background: #DCE4F5;
}

.walk-text {
  font-size: 10px;
  color: #9198a7;
  white-space: nowrap;
  background: white;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #DCE4F5;
}

.day-summary {
  margin-top: 16px;
  margin-bottom: 6px;
  padding: 12px 14px;
  background: #EDF4FC;
  border: 1px dashed #C5DEFF;
  border-radius: 14px;
  font-size: 12px;
  color: #6c7382;
  line-height: 1.7;
}

.diary-footer {
  margin-top: 8px;
  background: linear-gradient(135deg, #EDF4FC, #EAF3FF);
  border: 1px solid #C5DEFF;
  border-radius: 18px;
  padding: 14px 18px;
  color: #6d7281;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-logo {
  font-size: 16px;
  font-weight: 800;
  color: #FF9F6B;
}

@media (max-width: 480px) {
  .cover-title { font-size: 24px; }
  .day-title { font-size: 18px; }
  .poi-name { font-size: 14px; }
}
</style>
