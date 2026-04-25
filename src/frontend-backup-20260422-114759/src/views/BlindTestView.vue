<template>
  <div class="blind-test-view">
    <div class="page-header">
      <h1>盲测对比</h1>
      <p class="subtitle">对比 A/B/C 三组行程，选择你最喜欢的</p>
    </div>

    <div v-if="loading" class="loading"><n-spin size="large" /></div>
    <div v-else-if="error" class="error"><n-result status="error" title="加载失败" :description="error" /></div>
    <div v-else>
      <div v-for="scen in scenarios" :key="scen.id" class="scenario-block">
        <h3 class="scen-name">{{ scen.name }}</h3>
        <p class="scen-desc">{{ scen.description }}</p>
        <div class="itinerary-panels">
          <div v-for="(item, g) in scen.itineraries" :key="g" class="panel">
            <div class="panel-label">组别 {{ g }}</div>
            <div class="panel-content">{{ formatPlainText(item.itinerary) }}</div>
            <n-button size="small" class="vote-btn" @click="selectChoice(scen.id, g as string, item.id)">选择这个</n-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NSpin, NResult, NButton } from 'naive-ui'

const scenarios = ref<Array<{
  id: string
  name: string
  description: string
  itineraries: Record<string, { id: string; itinerary: Record<string, unknown> }>
}>>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await fetch('/api/scenarios')
    const scenList = await res.json()
    for (const s of scenList) {
      const r = await fetch(`/api/scenarios/${s.id}/itineraries`)
      const data = await r.json()
      scenarios.value.push({ ...s, itineraries: data.itineraries || {} })
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})

function formatPlainText(itinerary: Record<string, unknown>): string {
  if (!itinerary || !itinerary.days) return ''
  const lines: string[] = []
  for (const day of itinerary.days as Array<{ day_number: number; theme: string; pois: Array<{ time_slot: string; name: string; vibe_description: string }> }>) {
    lines.push(`第${day.day_number}天 · ${day.theme}`)
    for (const poi of day.pois) {
      lines.push(`  ${poi.time_slot} ${poi.name} — ${poi.vibe_description}`)
    }
    lines.push('')
  }
  return lines.join('\n')
}

async function selectChoice(scenarioId: string, group: string, itineraryId: string) {
  try {
    const r = await fetch('/api/test-results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario_id: scenarioId,
        participant_id: 'anonymous',
        group,
        preferred_itinerary_id: itineraryId,
      }),
    })
    if (r.ok) {
      alert(`已选择组别 ${group}`)
    } else {
      alert('提交失败，请重试')
    }
  } catch {
    alert('网络错误，请重试')
  }
}
</script>

<style scoped>
.blind-test-view { max-width: 900px; margin: 0 auto; padding: 24px 16px; }
.page-header { margin-bottom: 32px; }
.page-header h1 { font-size: 24px; font-weight: 700; margin: 0 0 8px; }
.subtitle { color: #999; margin: 0; }
.loading { display: flex; justify-content: center; padding: 60px; }
.error { padding: 40px; }
.scenario-block { margin-bottom: 40px; }
.scen-name { font-size: 18px; font-weight: 700; margin: 0 0 6px; }
.scen-desc { font-size: 14px; color: #666; margin: 0 0 16px; }
.itinerary-panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.panel {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}
.panel-label { font-size: 12px; font-weight: 700; color: #18a058; margin-bottom: 8px; text-transform: uppercase; }
.panel-content { font-size: 13px; white-space: pre-wrap; color: #444; margin-bottom: 12px; min-height: 100px; }
.vote-btn { min-height: 44px; min-width: 44px; }

@media (max-width: 768px) {
  .blind-test-view { padding: 16px 12px; }
  .page-header h1 { font-size: 20px; }
  .itinerary-panels { grid-template-columns: 1fr; }
  .panel { padding: 12px; }
  .panel-content { font-size: 12px; min-height: 60px; }
}
</style>
