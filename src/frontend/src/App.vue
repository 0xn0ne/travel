<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <AppHeader @open-login="authModal?.openLogin()" />
        <AuthModal ref="authModal" />
        <router-view />
        <ChatBubble />
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
import ChatBubble from '@/components/ChatBubble.vue'

const route = useRoute()
const authModal = ref<InstanceType<typeof AuthModal> | null>(null)

const themeOverrides = {
  common: {
    primaryColor: '#FF6B6B',
    primaryColorHover: '#FF8A8A',
    primaryColorPressed: '#E55A5A',
    primaryColorSuppl: '#FF6B6B',
    successColor: '#4ECDC4',
    successColorHover: '#6FE0D8',
    successColorPressed: '#3DBDB4',
    warningColor: '#F59E0B',
    warningColorHover: '#FBBF24',
    warningColorPressed: '#D97706',
    errorColor: '#FF6B6B',
    errorColorHover: '#FF8A8A',
    errorColorPressed: '#E55A5A',
    textColorBase: '#2D2016',
    textColor1: '#2D2016',
    textColor2: '#4A3F35',
    textColor3: '#6B5B4E',
    bodyColor: '#FFFAF5',
    cardColor: '#FFFFFF',
    modalColor: '#FFFFFF',
    popoverColor: '#FFFFFF',
    tableColor: '#FFFAF5',
    inputColor: '#FFF8F0',
    actionColor: '#F5E6D3',
    borderColor: '#E8D5C4',
    dividerColor: '#E8D5C4',
    borderRadius: '16px',
    borderRadiusSmall: '8px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  Card: {
    borderRadius: '16px',
    color: '#FFFFFF',
    borderColor: '#E8D5C4',
    boxShadow: '0 2px 12px rgba(45, 32, 22, 0.08)',
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
    borderFocus: '1px solid #FF6B6B',
    borderHover: '1px solid #E8D5C4',
    borderFocusWarning: '1px solid #F59E0B',
    borderFocusError: '1px solid #E55A5A',
    borderHoverWarning: '1px solid #F59E0B',
    borderHoverError: '1px solid #E55A5A',
    color: '#FFF8F0',
  },
  Alert: {
    titleFontSize: '14px',
    colorWarning: '#FEF3C7',
    colorError: '#FFF5F5',
    colorInfo: '#6FE0D8',
    borderWarning: '1px solid #F59E0B',
    borderError: '1px solid #FF6B6B',
    iconColorWarning: '#F59E0B',
    iconColorError: '#FF6B6B',
  },
  Empty: {
    iconColor: '#4ECDC4',
    textColor: '#6B5B4E',
  },
  Spin: {
    textColor: '#FF6B6B',
  },
  Skeleton: {
    color: '#F5E6D3',
    colorEnd: '#E8DDD3',
  },
}

onMounted(() => {
  if (route.query.login === 'required') {
    authModal.value?.openLogin()
  }
})
</script>
