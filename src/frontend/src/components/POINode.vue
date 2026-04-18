<template>
  <div
    class="poi-card"
    :class="{
      'preview-add': previewMode && changeType === 'add',
      'preview-replace': previewMode && changeType === 'replace',
      'preview-delete': previewMode && changeType === 'delete',
    }"
  >
    <!-- Preview: Change tag -->
    <div v-if="previewMode && changeType" class="change-tag" :class="'tag-' + changeType">
      {{ changeTypeLabel }}
    </div>

    <!-- Preview: Replaced POI name (struck through) -->
    <div v-if="previewMode && changeType === 'replace' && replacedPoi" class="replaced-poi">
      <span class="replaced-name">{{ replacedPoi.name }}</span>
      <span class="replaced-time">{{ replacedPoi.time_slot }}</span>
    </div>

    <!-- Summary row (clickable expand/collapse) -->
    <div
      class="poi-summary"
      role="button"
      tabindex="0"
      :aria-expanded="expanded"
      @click="$emit('toggle')"
      @keydown.enter="$emit('toggle')"
      @keydown.space.prevent="$emit('toggle')"
    >
      <!-- Left: time_slot -->
      <span class="poi-time">{{ poi.time_slot }}</span>

      <!-- Middle: tier badge + name + data source tag -->
      <div class="poi-identity">
        <span class="tier-badge" :style="{ background: tierConfig.bgVar }" :title="'Tier ' + tierConfig.label">
          {{ tierConfig.symbol }}
        </span>
        <span class="poi-name">{{ poi.name }}</span>
        <span class="source-tag" :style="{ color: dataSource.color, borderColor: dataSource.color }">
          <!-- Star icon (curated) -->
          <svg v-if="dataSource.icon === 'star'" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" class="source-icon">
            <path d="M8 1l2.24 4.54L15 6.27l-3.5 3.41.83 4.82L8 12.27l-4.33 2.23.83-4.82L1 6.27l4.76-.73L8 1z"/>
          </svg>
          <!-- Pin icon (amap) -->
          <svg v-if="dataSource.icon === 'pin'" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" class="source-icon">
            <path d="M8 1C5.24 1 3 3.24 3 6c0 3.75 5 9 5 9s5-5.25 5-9c0-2.76-2.24-5-5-5zm0 7.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z"/>
          </svg>
          <!-- Sparkle icon (AI) -->
          <svg v-if="dataSource.icon === 'sparkle'" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" class="source-icon">
            <path d="M8 0l1.5 5.5L15 8l-5.5 2.5L8 16l-1.5-5.5L1 8l5.5-2.5L8 0zm-4.5.5l.75 2.75L3 4l1.25.75L5 7.5l.75-2.75L7 4l-1.25-.75L6.5.5 5.75 3.25 4.5 4l1.25.75L3.5 7.5z"/>
          </svg>
          <span class="source-label">{{ dataSource.label }}</span>
        </span>
      </div>

      <!-- Right: chevron -->
      <svg
        class="chevron"
        :class="{ 'chevron-open': expanded }"
        viewBox="0 0 16 16"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M4 6l4 4 4-4"/>
      </svg>
    </div>

    <!-- Preview: Action toolbar -->
    <div v-if="previewMode" class="action-toolbar" @click.stop>
      <button class="action-btn" title="替换" @click="$emit('action', 'replace', poi)">替换</button>
      <button class="action-btn action-btn-danger" title="删除" @click="$emit('action', 'delete', poi)">删除</button>
      <button class="action-btn" title="前面插入" @click="$emit('action', 'insert_before', poi)">前插</button>
      <button class="action-btn" title="后面插入" @click="$emit('action', 'insert_after', poi)">后插</button>
    </div>

    <!-- Expanded detail -->
    <Transition name="expand">
      <div v-if="expanded" class="poi-detail">
        <div v-if="poi.highlight_note" class="detail-section">
          <span class="detail-label">推荐理由</span>
          <p class="detail-text">{{ poi.highlight_note }}</p>
        </div>
        <div class="detail-section">
          <span class="detail-label">氛围</span>
          <p class="detail-text">{{ poi.vibe_description }}</p>
        </div>
        <div v-if="poi.walk_to_next_minutes" class="detail-row">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" class="detail-icon">
            <path d="M9.5 1.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 5L5 15h2l1-4 1 4h2L9.5 5h-3zm-1 3L4 12l1.5.5L7 8.5 5.5 8z"/>
          </svg>
          <span class="detail-muted">步行 {{ poi.walk_to_next_minutes }} 分钟到下一站</span>
        </div>
        <div class="detail-row">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" class="detail-icon">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 12.5a5.5 5.5 0 110-11 5.5 5.5 0 010 11zM8.5 4H7v4.25l3.5 2.1.75-1.24-2.75-1.65V4z"/>
          </svg>
          <span class="detail-muted">暂无营业时间</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { POIVisitData } from '../types/itinerary'

const props = defineProps<{
  poi: POIVisitData
  expanded: boolean
  previewMode?: boolean
  changeType?: 'add' | 'replace' | 'delete' | null
  replacedPoi?: POIVisitData | null
}>()

defineEmits<{
  toggle: []
  action: [type: 'replace' | 'delete' | 'insert_before' | 'insert_after', poi: POIVisitData]
}>()

const changeTypeLabel = computed(() => {
  switch (props.changeType) {
    case 'add': return '新增'
    case 'replace': return '替换'
    case 'delete': return '删除'
    default: return ''
  }
})

const tierConfig = computed(() => {
  const tier = props.poi?.tier || 2
  const configs: Record<number, { symbol: string; bgVar: string; label: string }> = {
    1: { symbol: '\u2605', bgVar: 'var(--color-tier-gold)', label: 'A' },
    2: { symbol: '\u25CB', bgVar: 'var(--color-tier-silver)', label: 'B' },
    3: { symbol: '\u25C7', bgVar: 'var(--color-tier-bronze)', label: 'C' },
  }
  return configs[tier] || configs[2]
})

const dataSource = computed(() => {
  const tier = props.poi?.tier
  if (tier === 1) return { label: '人工精选', color: 'var(--color-source-curated)', icon: 'star' }
  if (tier === 2) return { label: '高德地图', color: 'var(--color-source-amap)', icon: 'pin' }
  return { label: 'AI推荐', color: 'var(--color-source-ai)', icon: 'sparkle' }
})
</script>

<style scoped>
.poi-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  background: white;
  border: 1px solid var(--color-warm-border);
  padding: 14px 16px;
  transition: var(--transition-smooth);
  border-left: 4px solid transparent;
}
.poi-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

/* === Change Tags (preview mode) === */
.change-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  line-height: 1.4;
  font-weight: 500;
  white-space: nowrap;
  margin-bottom: 8px;
  display: inline-block;
  width: fit-content;
}
.tag-add {
  background: color-mix(in srgb, var(--color-ocean) 12%, white);
  color: var(--color-ocean-dark);
}
.tag-replace {
  background: color-mix(in srgb, var(--color-coral) 12%, white);
  color: var(--color-coral-dark);
}
.tag-delete {
  background: color-mix(in srgb, var(--color-coral) 12%, white);
  color: var(--color-coral-dark);
}

/* === Replaced POI (preview mode) === */
.replaced-poi {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0 6px;
  font-size: 13px;
  color: var(--color-warm-text-muted);
}
.replaced-name {
  text-decoration: line-through;
}
.replaced-time {
  font-size: 12px;
}

/* === Summary Row === */
.poi-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.poi-time {
  font-size: 13px;
  color: var(--color-warm-text-muted);
  min-width: 80px;
  flex-shrink: 0;
}
.poi-identity {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.poi-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-warm-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* === Tier Badge === */
.tier-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 11px;
  line-height: 1;
  color: white;
  flex-shrink: 0;
}

/* === Data Source Tag === */
.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  border-radius: 6px;
  padding: 2px 8px;
  background: white;
  border: 1px solid;
  border-color: inherit;
  opacity: 0.85;
  flex-shrink: 0;
  white-space: nowrap;
}
.source-icon {
  flex-shrink: 0;
}
.source-label {
  line-height: 1;
}

/* === Chevron === */
.chevron {
  flex-shrink: 0;
  color: var(--color-warm-text-muted);
  transition: transform 0.2s ease;
}
.chevron-open {
  transform: rotate(180deg);
}

/* === Action Toolbar (preview mode) === */
.action-toolbar {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}
.action-btn {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--color-warm-border);
  border-radius: 8px;
  background: white;
  color: var(--color-warm-text);
  cursor: pointer;
  line-height: 1.4;
  white-space: nowrap;
  min-height: 32px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-smooth);
}
.action-btn:hover {
  background: var(--color-warm-surface);
}
.action-btn-danger {
  color: var(--color-coral);
}
.action-btn-danger:hover {
  background: color-mix(in srgb, var(--color-coral) 10%, white);
  border-color: var(--color-coral-light);
}

/* === Expanded Detail === */
.poi-detail {
  overflow: hidden;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-warm-border);
}
.detail-section {
  margin-bottom: 10px;
}
.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ocean);
  display: block;
  margin-bottom: 4px;
}
.detail-text {
  font-size: 14px;
  color: var(--color-warm-text);
  line-height: 1.6;
  margin: 0;
}
.detail-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}
.detail-icon {
  flex-shrink: 0;
  color: var(--color-warm-text-muted);
}
.detail-muted {
  font-size: 13px;
  color: var(--color-warm-text-muted);
}

/* === Preview Mode Border-Left === */
.preview-add {
  border-left-color: var(--color-ocean);
}
.preview-replace {
  border-left-color: var(--color-coral);
}
.preview-delete {
  border-left-color: var(--color-coral);
  opacity: 0.55;
}
.preview-delete .poi-summary {
  text-decoration: line-through;
}

/* === Expand/Collapse Transition === */
.expand-enter-active,
.expand-leave-active {
  transition: max-height 0.3s ease, opacity 0.3s ease;
  max-height: 400px;
  opacity: 1;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
