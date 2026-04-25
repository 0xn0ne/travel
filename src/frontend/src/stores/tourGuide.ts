import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/** Generate a UUID v4 — works in both secure and non-secure contexts */
function uuid(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

export interface TourGuideProfile {
  visitedPois: string[]
  preferences: string[]
  budget: string
  pace: string
}

export interface GuideMessage {
  id: string
  role: 'user' | 'guide'
  content: string
  timestamp: string
  isStreaming?: boolean
}

export interface TourGuideState {
  observations: string[]
  profile: TourGuideProfile
  messages: GuideMessage[]
  isStreaming: boolean
  streamingText: string
  toolStatus: string | null
  sessionId: string
}

const STORAGE_KEY = 'tour-guide-profile'

function loadProfile(): TourGuideProfile {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch {}
  return {
    visitedPois: [],
    preferences: [],
    budget: '',
    pace: '',
  }
}

export const useTourGuideStore = defineStore('tourGuide', () => {
  const observations = ref<string[]>([])
  const profile = ref<TourGuideProfile>(loadProfile())
  const messages = ref<GuideMessage[]>([])
  const isStreaming = ref(false)
  const streamingText = ref('')
  const toolStatus = ref<string | null>(null)
  const sessionId = ref(uuid())

  watch(profile, (newProfile) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newProfile))
  }, { deep: true })

  function addObservation(text: string) {
    if (text.trim()) {
      observations.value.push(text.trim())
    }
  }

  function removeObservation(index: number) {
    observations.value.splice(index, 1)
  }

  function updateProfile(field: keyof TourGuideProfile, value: string | string[]) {
    if (field === 'visitedPois' || field === 'preferences') {
      (profile.value[field] as string[]) = value as string[]
    } else {
      (profile.value[field] as string) = value as string
    }
  }

  function addUserMessage(content: string) {
    messages.value.push({
      id: uuid(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    })
  }

  function addGuideMessage(content: string, isStreamingFlag = false): string {
    const id = uuid()
    const msg: GuideMessage = {
      id,
      role: 'guide',
      content,
      timestamp: new Date().toISOString(),
      isStreaming: isStreamingFlag,
    }
    messages.value.push(msg)
    return id
  }

  function updateGuideMessage(id: string, updates: Partial<GuideMessage>) {
    const idx = messages.value.findIndex(m => m.id === id)
    if (idx !== -1) {
      messages.value[idx] = { ...messages.value[idx], ...updates }
    }
  }

  function updateStreamingText(text: string) {
    streamingText.value = text
  }

  function setStreaming(val: boolean) {
    isStreaming.value = val
  }

  function setToolStatus(status: string | null) {
    toolStatus.value = status
  }

  function resetSession() {
    observations.value = []
    messages.value = []
    isStreaming.value = false
    streamingText.value = ''
    toolStatus.value = null
    sessionId.value = uuid()
  }

  return {
    observations,
    profile,
    messages,
    isStreaming,
    streamingText,
    toolStatus,
    sessionId,
    addObservation,
    removeObservation,
    updateProfile,
    addUserMessage,
    addGuideMessage,
    updateGuideMessage,
    updateStreamingText,
    setStreaming,
    setToolStatus,
    resetSession,
  }
})