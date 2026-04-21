<template>
  <div class="diary-view">
    <!-- 顶部封面 -->
    <div class="diary-cover">
      <div class="cover-title">{{ title || '旅行手帐' }}</div>
      <div class="cover-meta">
        <span class="cover-tag">📅 {{ dateRange }}</span>
        <span class="cover-tag">👫 {{ peopleCount }}</span>
        <span class="cover-tag">🏃 {{ totalDistance }}</span>
        <span class="cover-weather" v-if="weather">{{ weather }}</span>
      </div>
      <div class="cover-taste-tags" v-if="tasteTags && tasteTags.length">
        <span v-for="tag in tasteTags" :key="tag" class="taste-tag">{{ tag }}</span>
      </div>
    </div>

    <!-- 每日手帐 -->
    <div
      v-for="day in days"
      :key="day.day_number"
      class="day-diary"
    >
      <!-- 左侧时间线装饰 -->
      <div class="timeline-rail">
        <div class="timeline-dot" />
        <div class="timeline-line" />
      </div>

      <!-- Day 内容 -->
      <div class="day-content">
        <!-- Day 标题 -->
        <div class="day-header">
          <div class="day-title">
            {{ day.theme || `Day ${day.day_number}` }}
          </div>
          <div class="day-date" v-if="(day as any).date">{{ (day as any).date }}</div>
        </div>

        <!-- POI 列表 -->
        <div class="poi-list">
          <div
            v-for="(poi, idx) in day.pois"
            :key="idx"
            class="poi-card"
            :class="{ highlighted: highlightedId === poi.poi_id }"
            @click="handlePoiClick(poi)"
          >
            <!-- emoji 图标 -->
            <div class="poi-emoji">{{ getPoiEmoji(poi) }}</div>

            <!-- 卡片内容 -->
            <div class="poi-body">
              <div class="poi-time">{{ poi.time_slot }}</div>
              <div class="poi-name">{{ poi.name }}</div>
              <div class="poi-vibe" v-if="poi.vibe_description">{{ poi.vibe_description }}</div>
              <div class="poi-note" v-if="poi.highlight_note">
                <span class="note-icon">💡</span>
                {{ poi.highlight_note }}
              </div>
            </div>

            <!-- 步行时间 -->
            <div class="walk-to-next" v-if="poi.walk_to_next_minutes && idx < day.pois.length - 1">
              <div class="walk-line" />
              <span class="walk-text">🚶 {{ poi.walk_to_next_minutes }}分钟</span>
            </div>
          </div>
        </div>

        <!-- 每日小结 -->
        <div class="day-summary" v-if="(day as any).summary">
          ✨ {{ (day as any).summary }}
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <div class="diary-footer">
      <span>用心记录每一次出发</span>
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

// emoji 映射
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
  if (text.includes('豫园')) return '🏯'
  if (text.includes('西湖')) return '🌊'
  if (text.includes('咖啡')) return '☕'
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

/* ===== 封面 ===== */
.diary-cover {
  background: linear-gradient(135deg, #FFB5B5 0%, #FFA0A0 50%, #FF8E8E 100%);
  border-radius: 16px;
  padding: 24px 20px 18px;
  color: white;
  position: relative;
  overflow: hidden;
  margin-bottom: 4px;
}

.diary-cover::before {
  content: '';
  position: absolute;
  top: -30px;
  right: -30px;
  width: 140px;
  height: 140px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

.diary-cover::after {
  content: '';
  position: absolute;
  bottom: -20px;
  left: 25%;
  width: 60px;
  height: 60px;
  background: rgba(255,255,255,0.08);
  border-radius: 50%;
}

.cover-title {
  font-family: 'Ma Shan Zheng', cursive, 'PingFang SC', sans-serif;
  font-size: 28px;
  color: white;
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
}

.cover-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  position: relative;
  z-index: 1;
}

.cover-tag {
  font-size: 11px;
  background: rgba(255,255,255,0.2);
  padding: 3px 10px;
  border-radius: 20px;
  color: white;
}

.cover-weather {
  font-size: 11px;
  background: rgba(255,255,255,0.2);
  padding: 3px 10px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.cover-taste-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 10px;
  position: relative;
  z-index: 1;
}

.taste-tag {
  font-size: 10px;
  background: rgba(255,255,255,0.25);
  border: 1px solid rgba(255,255,255,0.3);
  padding: 2px 8px;
  border-radius: 12px;
  color: white;
}

/* ===== 每日手帐 ===== */
.day-diary {
  display: flex;
  gap: 0;
  position: relative;
  background: white;
  border-left: 1.5px solid rgba(255,107,107,0.12);
  border-right: 1.5px solid rgba(255,107,107,0.12);
  border-bottom: 1px dashed rgba(255,107,107,0.1);
}

.day-diary:last-of-type {
  border-radius: 0 0 16px 16px;
  border-bottom: 1.5px solid rgba(255,107,107,0.15);
}

/* 左侧时间线 */
.timeline-rail {
  width: 36px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 24px;
  position: relative;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 3px solid #FF8E8E;
  background: white;
  z-index: 1;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(255,142,142,0.15);
}

.timeline-dot::after {
  content: '';
  position: absolute;
  inset: 2px;
  background: #FF8E8E;
  border-radius: 50%;
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(to bottom, #FF8E8E, rgba(255,107,107,0.1));
  margin-top: 4px;
  min-height: 40px;
}

/* Day 内容 */
.day-content {
  flex: 1;
  padding: 20px 16px 16px 0;
}

.day-header {
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255,107,107,0.07);
}

.day-title {
  font-family: 'Ma Shan Zheng', cursive, 'PingFang SC', sans-serif;
  font-size: 22px;
  color: #FF6B6B;
  margin-bottom: 2px;
}

.day-date {
  font-size: 11px;
  color: #ccc;
}

/* ===== POI 卡片 ===== */
.poi-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.poi-card {
  display: flex;
  gap: 0;
  position: relative;
  background: #FFFDFB;
  border: 1px solid rgba(255,107,107,0.08);
  border-radius: 12px;
  padding: 12px 12px 10px 12px;
  box-shadow: 0 2px 6px rgba(255,107,107,0.04);
  transition: all 0.2s;
  cursor: pointer;
}

.poi-card:hover {
  transform: translateX(3px);
  box-shadow: 0 4px 14px rgba(255,107,107,0.1);
  border-color: rgba(255,107,107,0.18);
}

.poi-card.highlighted {
  border-color: #FF8E8E;
  box-shadow: 0 4px 16px rgba(255,107,107,0.15);
  background: #FFF9F9;
}

/* 卡片顶部渐变条 */
.poi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #FFB5B5, #FF8E8E, #FFD4D4);
  border-radius: 12px 12px 0 0;
}

/* emoji 图标 */
.poi-emoji {
  width: 34px;
  height: 34px;
  background: white;
  border: 2px solid #FF8E8E;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  margin-right: 10px;
  margin-top: 2px;
  box-shadow: 0 2px 6px rgba(255,107,107,0.12);
  position: relative;
  z-index: 1;
}

/* 卡片主体 */
.poi-body {
  flex: 1;
  min-width: 0;
}

.poi-time {
  font-size: 10px;
  color: #FF9999;
  font-weight: 600;
  margin-bottom: 3px;
  letter-spacing: 0.3px;
}

.poi-name {
  font-size: 14px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 4px;
  line-height: 1.3;
}

.poi-vibe {
  font-size: 11px;
  color: #999;
  font-style: italic;
  line-height: 1.5;
  margin-bottom: 6px;
}

/* 贴士框 */
.poi-note {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  background: #FFF9F5;
  border: 1px solid rgba(255,180,100,0.18);
  border-radius: 8px;
  padding: 6px 9px;
  font-size: 11px;
  color: #8B6347;
  line-height: 1.5;
}

.note-icon {
  font-size: 11px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* 步行时间 */
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
  background: #FFD0D0;
}

.walk-text {
  font-size: 10px;
  color: #ccc;
  white-space: nowrap;
  background: white;
  padding: 1px 6px;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

/* ===== 每日小结 ===== */
.day-summary {
  margin-top: 16px;
  margin-bottom: 8px;
  padding: 10px 14px;
  background: #FFF9F5;
  border: 1px dashed rgba(255,107,107,0.2);
  border-radius: 10px;
  font-size: 11px;
  color: #8B6914;
  line-height: 1.6;
}

/* ===== 底部 ===== */
.diary-footer {
  margin-top: 4px;
  background: linear-gradient(135deg, #FFB5B5, #FFA0A0);
  border-radius: 0 0 16px 16px;
  padding: 14px 20px;
  color: white;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  opacity: 0.9;
}

.footer-logo {
  font-family: 'Ma Shan Zheng', cursive, 'PingFang SC', sans-serif;
  font-size: 18px;
}

/* ===== 字体加载 ===== */
@import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&display=swap');

/* ===== 响应式 ===== */
@media (max-width: 480px) {
  .cover-title { font-size: 24px; }
  .day-title { font-size: 20px; }
  .poi-name { font-size: 13px; }
}
</style>
