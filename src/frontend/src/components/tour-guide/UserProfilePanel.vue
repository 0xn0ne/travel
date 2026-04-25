<template>
  <div class="profile-panel-card">
    <div class="section-header">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
      <span>我的旅行画像</span>
      <button class="edit-btn" @click="isEditing = !isEditing">
        <svg v-if="!isEditing" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div v-if="!isEditing" class="profile-display">
      <div v-if="store.profile.visitedPois.length > 0" class="profile-section">
        <span class="profile-label">去过的地方</span>
        <div class="tag-row">
          <span v-for="poi in store.profile.visitedPois" :key="poi" class="profile-tag">
            {{ poi }}
          </span>
        </div>
      </div>

      <div v-if="store.profile.preferences.length > 0" class="profile-section">
        <span class="profile-label">偏好标签</span>
        <div class="tag-row">
          <span v-for="pref in store.profile.preferences" :key="pref" class="profile-tag teal">
            {{ pref }}
          </span>
        </div>
      </div>

      <div v-if="store.profile.budget" class="profile-section">
        <span class="profile-label">预算</span>
        <span class="profile-badge">{{ store.profile.budget }}</span>
      </div>

      <div v-if="store.profile.pace" class="profile-section">
        <span class="profile-label">节奏</span>
        <span class="profile-badge teal">{{ store.profile.pace }}</span>
      </div>

      <p v-if="store.profile.visitedPois.length === 0 && store.profile.preferences.length === 0 && !store.profile.budget && !store.profile.pace" class="empty-hint">
        点击编辑完善你的旅行画像
      </p>
    </div>

    <div v-else class="profile-edit">
      <div class="edit-section">
        <span class="edit-label">去过的城市/景点</span>
        <div class="add-poi-row">
          <input
            v-model="newPoi"
            class="edit-input"
            placeholder="添加城市或景点"
            @keydown.enter="addPoi"
          />
          <button class="add-btn" @click="addPoi">+</button>
        </div>
        <div v-if="store.profile.visitedPois.length > 0" class="tag-row">
          <span v-for="poi in store.profile.visitedPois" :key="poi" class="profile-tag removable" @click="removePoi(poi)">
            {{ poi }}
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </span>
        </div>
      </div>

      <div class="edit-section">
        <span class="edit-label">偏好标签</span>
        <div class="pref-tags">
          <button
            v-for="pref in preferenceOptions"
            :key="pref"
            :class="['pref-tag', { active: store.profile.preferences.includes(pref) }]"
            @click="togglePref(pref)"
          >
            {{ pref }}
          </button>
        </div>
      </div>

      <div class="edit-section">
        <span class="edit-label">预算</span>
        <div class="pill-group">
          <button
            v-for="budget in ['节俭', '适中', '宽裕']"
            :key="budget"
            :class="['pill', { active: store.profile.budget === budget }]"
            @click="store.updateProfile('budget', budget)"
          >
            {{ budget }}
          </button>
        </div>
      </div>

      <div class="edit-section">
        <span class="edit-label">节奏</span>
        <div class="pill-group">
          <button
            v-for="pace in ['悠闲', '适中', '紧凑']"
            :key="pace"
            :class="['pill teal', { active: store.profile.pace === pace }]"
            @click="store.updateProfile('pace', pace)"
          >
            {{ pace }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTourGuideStore } from '@/stores/tourGuide'

const store = useTourGuideStore()
const isEditing = ref(false)
const newPoi = ref('')

const preferenceOptions = ['咖啡控', '文艺青年', '小众探索', '美食家', '历史迷', '自然风光', '夜生活', '摄影', '购物', '慢旅行']

function addPoi() {
  const poi = newPoi.value.trim()
  if (poi && !store.profile.visitedPois.includes(poi)) {
    store.updateProfile('visitedPois', [...store.profile.visitedPois, poi])
    newPoi.value = ''
  }
}

function removePoi(poi: string) {
  store.updateProfile('visitedPois', store.profile.visitedPois.filter(p => p !== poi))
}

function togglePref(pref: string) {
  const current = store.profile.preferences
  if (current.includes(pref)) {
    store.updateProfile('preferences', current.filter(p => p !== pref))
  } else {
    store.updateProfile('preferences', [...current, pref])
  }
}
</script>

<style scoped>
.profile-panel-card {
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
  color: #FF6B6B;
}

.edit-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #6B5B4E;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}

.edit-btn:hover {
  background: #FFF8F0;
}

.profile-display {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-label {
  font-size: 12px;
  color: #6B5B4E;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.profile-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 107, 107, 0.1);
  color: #FF6B6B;
  font-size: 12px;
  font-weight: 500;
}

.profile-tag.teal {
  background: rgba(78, 205, 196, 0.1);
  color: #4ECDC4;
}

.profile-tag.removable {
  cursor: pointer;
}

.profile-tag.removable:hover {
  background: rgba(255, 107, 107, 0.2);
}

.profile-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 107, 107, 0.1);
  color: #FF6B6B;
  font-size: 12px;
  font-weight: 500;
}

.profile-badge.teal {
  background: rgba(78, 205, 196, 0.1);
  color: #4ECDC4;
}

.empty-hint {
  color: #6B5B4E;
  font-size: 12px;
  text-align: center;
  padding: 8px;
}

.profile-edit {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.edit-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.edit-label {
  font-size: 12px;
  color: #6B5B4E;
  font-weight: 500;
}

.add-poi-row {
  display: flex;
  gap: 6px;
}

.edit-input {
  flex: 1;
  border: 1px solid #E8D5C4;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 13px;
  outline: none;
  background: #FFF8F0;
  color: #2D2016;
  transition: border-color 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.edit-input:focus {
  border-color: #FF6B6B;
}

.add-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #4ECDC4;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #3DBDB4;
}

.pref-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pref-tag {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #E8D5C4;
  background: #FFF8F0;
  color: #6B5B4E;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.pref-tag.active {
  background: #FF6B6B;
  color: white;
  border-color: #FF6B6B;
}

.pref-tag:hover:not(.active) {
  border-color: #FF6B6B;
  color: #FF6B6B;
}

.pill-group {
  display: flex;
  gap: 6px;
}

.pill {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid #E8D5C4;
  background: #FFF8F0;
  color: #6B5B4E;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.pill.active {
  background: #FF6B6B;
  color: white;
  border-color: #FF6B6B;
}

.pill.teal.active {
  background: #4ECDC4;
  border-color: #4ECDC4;
}

.pill:hover:not(.active) {
  border-color: #FF6B6B;
  color: #FF6B6B;
}

.pill.teal:hover:not(.active) {
  border-color: #4ECDC4;
  color: #4ECDC4;
}
</style>