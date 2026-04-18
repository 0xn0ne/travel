<template>
  <div
    class="sticky bottom-0 w-full md:max-w-md border-t border-[var(--color-warm-border)] bg-[var(--color-warm-surface)]/90 backdrop-blur-sm p-4"
  >
    <template v-if="submitError">
      <p class="text-center text-sm text-[var(--color-coral)]">提交失败，请重试</p>
      <NButton size="small" @click="submitError = false" class="mt-2">重试</NButton>
    </template>
    <template v-else-if="submitted">
      <p class="text-center text-sm text-[var(--color-warm-text-muted)]">感谢反馈！</p>
    </template>
    <template v-else-if="selectedRating">
        <p class="mb-2 text-sm text-[var(--color-warm-text)]">推荐准不准？</p>
        <NInput
          v-model:value="comment"
          type="textarea"
          placeholder="想补充点什么？（可选）"
          :rows="2"
          class="mb-2"
        />
        <NButton type="primary" size="small" @click="handleSubmit">提交</NButton>
      </template>
      <template v-else>
        <p class="mb-2 text-sm text-[var(--color-warm-text)]">推荐准不准？</p>
      <div class="flex gap-2">
        <NButton size="small" @click="selectRating('准')">准</NButton>
        <NButton size="small" @click="selectRating('一般')">一般</NButton>
        <NButton size="small" @click="selectRating('不准')">不准</NButton>
      </div>
    </template>
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
