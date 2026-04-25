<template>
  <n-button
    v-if="itineraryId"
    class="share-button"
    type="default"
    size="small"
    @click="handleShare"
  >
    <template #icon>
      <!-- Link/Share icon -->
      <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
        <path d="M4.5 8.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5zM8 5a2.5 2.5 0 015 0 2.5 2.5 0 01-5 0zm-2.5 6a2.5 2.5 0 010 5 2.5 2.5 0 010-5zM8 13.5a2.5 2.5 0 015 0 2.5 2.5 0 01-5 0z"/>
        <path d="M6.5 7.5l3-2M6.5 8.5l3 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </template>
    分享
  </n-button>
</template>

<script setup lang="ts">
import { NButton, useMessage } from 'naive-ui'

defineProps<{
  itineraryId: string
}>()

const message = useMessage()

async function handleShare() {
  const url = window.location.href
  
  try {
    // Try modern clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(url)
      showSuccessToast()
      return
    }
    
    // Fallback to document.execCommand
    const textArea = document.createElement('textarea')
    textArea.value = url
    textArea.style.position = 'fixed'
    textArea.style.left = '-999999px'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    
    if (successful) {
      showSuccessToast()
    } else {
      throw new Error('Copy command failed')
    }
  } catch (e) {
    console.error('Failed to copy:', e)
    message.error('复制失败，请手动复制链接')
  }
}

function showSuccessToast() {
  message.success('链接已复制，分享给朋友吧！', {
    duration: 3000,
  })
}
</script>

<style scoped>
.share-button {
  color: var(--color-primary);
  border-color: var(--color-primary-light);
}

.share-button:hover {
  color: var(--color-primary-dark);
  border-color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 8%, white);
}
</style>
