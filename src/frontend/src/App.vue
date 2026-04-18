<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <AppHeader @open-login="authModal?.openLogin()" />
        <AuthModal ref="authModal" />
        <router-view />
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NNotificationProvider } from 'naive-ui'
import AppHeader from '@/components/AppHeader.vue'
import AuthModal from '@/components/AuthModal.vue'

const route = useRoute()
const authModal = ref<InstanceType<typeof AuthModal> | null>(null)

const themeOverrides = {
  common: {
    primaryColor: 'var(--color-coral)',
    primaryColorHover: 'var(--color-coral-light)',
    primaryColorPressed: 'var(--color-coral-dark)',
    primaryColorSuppl: 'var(--color-coral)',
    successColor: 'var(--color-ocean)',
    successColorHover: 'var(--color-ocean-light)',
    successColorPressed: 'var(--color-ocean-dark)',
    warningColor: 'var(--color-warm-amber)',
    warningColorHover: '#FBBF24',
    warningColorPressed: '#D97706',
    errorColor: 'var(--color-coral)',
    errorColorHover: 'var(--color-coral-light)',
    errorColorPressed: 'var(--color-coral-dark)',
    textColorBase: 'var(--color-warm-text)',
    textColor1: 'var(--color-warm-text)',
    textColor2: '#4A3F35',
    textColor3: 'var(--color-warm-text-muted)',
    bodyColor: 'var(--color-warm-bg)',
    cardColor: '#FFFFFF',
    modalColor: '#FFFFFF',
    popoverColor: '#FFFFFF',
    tableColor: 'var(--color-warm-bg)',
    inputColor: 'var(--color-warm-surface)',
    actionColor: 'var(--color-sand)',
    borderColor: 'var(--color-warm-border)',
    dividerColor: 'var(--color-warm-border)',
    borderRadius: '16px',
    borderRadiusSmall: '8px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  Card: {
    borderRadius: 'var(--radius-card)',
    color: '#FFFFFF',
    borderColor: 'var(--color-warm-border)',
    boxShadow: 'var(--shadow-card)',
  },
  Button: {
    borderRadiusMedium: '12px',
    borderRadiusSmall: '8px',
  },
  Tag: {
    borderRadius: '8px',
  },
  Input: {
    borderRadius: '12px',
    borderFocus: `1px solid var(--color-coral)`,
    borderHover: `1px solid var(--color-warm-border)`,
    borderFocusWarning: `1px solid var(--color-warm-amber)`,
    borderFocusError: `1px solid var(--color-coral-dark)`,
    borderHoverWarning: `1px solid var(--color-warm-amber)`,
    borderHoverError: `1px solid var(--color-coral-dark)`,
    color: 'var(--color-warm-surface)',
  },
  Alert: {
    titleFontSize: '14px',
    colorWarning: 'var(--color-warm-amber-light)',
    colorError: '#FFF5F5',
    colorInfo: 'var(--color-ocean-light)',
    borderWarning: `1px solid var(--color-warm-amber)`,
    borderError: `1px solid var(--color-coral)`,
    iconColorWarning: 'var(--color-warm-amber)',
    iconColorError: 'var(--color-coral)',
  },
  Empty: {
    iconColor: 'var(--color-ocean)',
    textColor: 'var(--color-warm-text-muted)',
  },
  Spin: {
    textColor: 'var(--color-coral)',
  },
  Skeleton: {
    color: 'var(--color-sand)',
    colorEnd: 'var(--color-warm-gray)',
  },
}

onMounted(() => {
  if (route.query.login === 'required') {
    authModal.value?.openLogin()
  }
})
</script>
