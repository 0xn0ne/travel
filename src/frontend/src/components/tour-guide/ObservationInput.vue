<template>
  <div class="observation-input-card">
    <div class="section-header">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
      <span>我看到了...</span>
    </div>

    <div class="quick-tags">
      <button
        v-for="tag in quickTags"
        :key="tag"
        class="quick-tag"
        @click="addQuickTag(tag)"
      >
        {{ tag }}
      </button>
    </div>

    <div v-if="store.observations.length > 0" class="observation-tags">
      <span
        v-for="(obs, index) in store.observations"
        :key="index"
        class="obs-tag"
      >
        {{ obs }}
        <button class="remove-btn" @click="store.removeObservation(index)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </span>
    </div>

    <div class="input-row">
      <input
        v-model="inputText"
        class="obs-input"
        placeholder="添加更多..."
        @keydown.enter="handleAdd"
      />
      <button class="send-btn" @click="handleAdd">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <p v-if="store.observations.length === 0" class="empty-hint">
      选择标签或输入你看到的场景
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTourGuideStore } from '@/stores/tourGuide'

const store = useTourGuideStore()
const inputText = ref('')

const quickTags = ['景点', '餐厅', '咖啡', '商店', '风景', '建筑', '街头', '夜景']

function addQuickTag(tag: string) {
  store.addObservation(tag)
}

function handleAdd() {
  const text = inputText.value.trim()
  if (text) {
    store.addObservation(text)
    inputText.value = ''
  }
}
function flushInput() {
  const text = inputText.value.trim()
  if (text) {
    store.addObservation(text)
    inputText.value = ''
  }
}

defineExpose({ flushInput })
</script>

<style scoped>
.observation-input-card {
  background: #FFFFFF;
  border: 1px solid #E8D5C4;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(45, 32, 22, 0.08);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #2D2016;
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 12px;
}

.section-header svg {
  color: #4ECDC4;
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.quick-tag {
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid #E8D5C4;
  background: #FFF8F0;
  color: #6B5B4E;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.quick-tag:hover {
  background: #FF6B6B;
  color: white;
  border-color: #FF6B6B;
}

.observation-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.obs-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px 4px 12px;
  border-radius: 999px;
  background: rgba(255, 107, 107, 0.1);
  color: #FF6B6B;
  font-size: 13px;
  font-weight: 500;
}

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  color: #FF6B6B;
  transition: background 0.2s;
}

.remove-btn:hover {
  background: rgba(255, 107, 107, 0.2);
}

.input-row {
  display: flex;
  gap: 8px;
}

.obs-input {
  flex: 1;
  border: 1px solid #E8D5C4;
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 14px;
  outline: none;
  background: #FFF8F0;
  color: #2D2016;
  transition: border-color 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.obs-input:focus {
  border-color: #FF6B6B;
}

.obs-input::placeholder {
  color: #6B5B4E;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #FF6B6B;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.send-btn:hover {
  background: #E55A5A;
  transform: scale(1.05);
}

.empty-hint {
  color: #6B5B4E;
  font-size: 12px;
  margin-top: 8px;
  text-align: center;
}
</style>