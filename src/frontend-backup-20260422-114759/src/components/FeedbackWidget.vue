<template>
  <div class="feedback-float" :class="{ expanded: expanded }">
    <button v-if="!expanded" class="feedback-trigger" @click="expanded = true">
      推荐反馈
    </button>

    <div v-else class="feedback-panel">
      <button class="feedback-close" @click="expanded = false">×</button>

      <template v-if="submitError">
        <p class="feedback-title">提交失败，请重试</p>
        <NButton size="small" @click="submitError = false">重试</NButton>
      </template>

      <template v-else-if="submitted">
        <p class="feedback-title">感谢反馈！</p>
        <div class="feedback-actions">
          <NButton size="small" @click="expanded = false">关闭</NButton>
        </div>
      </template>

      <template v-else-if="selectedRating">
        <p class="feedback-title">推荐准不准？</p>
        <NInput
          v-model:value="comment"
          type="textarea"
          placeholder="想补充点什么？（可选）"
          :rows="3"
        />
        <div class="feedback-actions">
          <NButton type="primary" size="small" @click="handleSubmit">提交</NButton>
        </div>
      </template>

      <template v-else>
        <p class="feedback-title">推荐准不准？</p>
        <div class="feedback-rating-list">
          <button class="feedback-rating-btn" @click="selectRating('准')">准</button>
          <button class="feedback-rating-btn" @click="selectRating('一般')">一般</button>
          <button class="feedback-rating-btn" @click="selectRating('不准')">不准</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NButton, NInput } from 'naive-ui'
import { useItineraryStore } from '../stores/itinerary'

const props = defineProps<{
  itineraryId: string
}>()

const store = useItineraryStore()

const expanded = ref(false)
const selectedRating = ref<string | null>(null)
const comment = ref('')
const submitted = ref(false)
const submitError = ref(false)

function selectRating(rating: string) {
  selectedRating.value = rating
}

async function handleSubmit() {
  submitError.value = false
  const ok = await store.submitFeedback(props.itineraryId, selectedRating.value!, comment.value || undefined)
  if (ok) {
    submitted.value = true
  } else {
    submitError.value = true
  }
}
</script>

<style scoped>
.feedback-float {
  position: fixed;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 120;
}

.feedback-trigger {
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid #ded8eb;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14px 28px rgba(35, 38, 47, 0.12);
  color: #6a6480;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  padding-block: 12px;
}

.feedback-panel {
  position: relative;
  width: 220px;
  padding: 16px;
  border: 1px solid #e4dff3;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20px 40px rgba(35, 38, 47, 0.14);
  backdrop-filter: blur(10px);
}

.feedback-close {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 999px;
  background: #f5f2fb;
  color: #7a718f;
  cursor: pointer;
}

.feedback-title {
  font-size: 13px;
  font-weight: 700;
  color: #363d4b;
  margin: 0 0 12px;
  padding-right: 24px;
}

.feedback-rating-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feedback-rating-btn {
  min-height: 36px;
  border: 1px solid #e7e1f5;
  border-radius: 12px;
  background: #fff;
  color: #61596f;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s ease;
}

.feedback-rating-btn:hover {
  background: #faf7ff;
  border-color: #cfc1ef;
  color: #7c62d6;
}

.feedback-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .feedback-float {
    right: 10px;
    top: auto;
    bottom: 108px;
    transform: none;
  }

  .feedback-panel {
    width: 200px;
  }
}
</style>
