import { createRouter, createWebHistory } from 'vue-router'
import { useItineraryStore } from '@/stores/itinerary'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'entry', component: () => import('@/views/EntryView.vue') },
  { path: '/j', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/j/itinerary/:id', name: 'itinerary', component: () => import('@/views/ItineraryView.vue') },
  { path: '/p', name: 'pmap', component: () => import('@/views/PMapView.vue') },
  { path: '/itinerary/:id', name: 'itinerary-old', component: () => import('@/views/ItineraryView.vue') },
  { path: '/blind-test', name: 'blind-test', component: () => import('@/views/BlindTestView.vue') },
  { path: '/settings', name: 'settings', component: () => import('@/views/SettingsView.vue'), meta: { requiresAuth: true } },
  { path: '/my-itineraries', name: 'my-itineraries', component: () => import('@/views/ItineraryListView.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  // 1. Auth guard: redirect protected routes to home with login trigger
  if (to.meta.requiresAuth) {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) {
      next({ path: '/', query: { login: 'required' } })
      return
    }
  }

  // 2. Preserve existing generation-in-progress guard
  const store = useItineraryStore()
  if (store.isGenerating || store.isAdjusting) {
    const confirmed = window.confirm('行程正在生成中，确定要离开吗？')
    if (!confirmed) return next(false)
    store.abort()
  }

  next()
})

export default router
