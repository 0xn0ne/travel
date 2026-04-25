<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <AppHeader @open-login="authModal?.openLogin()" />
        <AuthModal ref="authModal" />
        <div class="app-bg">
          <router-view />
        </div>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NNotificationProvider, zhCN, dateZhCN } from 'naive-ui'
import AppHeader from '@/components/AppHeader.vue'
import AuthModal from '@/components/AuthModal.vue'

const route = useRoute()
const authModal = ref<InstanceType<typeof AuthModal> | null>(null)

const themeOverrides = {
  common: {
    primaryColor: '#A78BFA',
    primaryColorHover: '#B79BFB',
    primaryColorPressed: '#8F79DB',
    primaryColorSuppl: '#A78BFA',
    successColor: '#6FCF97',
    successColorHover: '#86EFAC',
    successColorPressed: '#57BA80',
    warningColor: '#F4C96B',
    warningColorHover: '#F7D98F',
    warningColorPressed: '#D9B04F',
    errorColor: '#F39AA8',
    errorColorHover: '#F7B2BD',
    errorColorPressed: '#E17F91',
    textColorBase: '#333333',
    textColor1: '#333333',
    textColor2: '#666A73',
    textColor3: '#8A8F9D',
    bodyColor: '#F5F6FA',
    cardColor: '#FFFFFF',
    modalColor: '#FFFFFF',
    popoverColor: '#FFFFFF',
    tableColor: '#FAFBFD',
    inputColor: '#FFFFFF',
    actionColor: '#F7F4FE',
    borderColor: '#E7E8EE',
    dividerColor: '#ECECF2',
    borderRadius: '16px',
    borderRadiusSmall: '10px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  Card: {
    borderRadius: '18px',
    color: '#FFFFFF',
    borderColor: '#E7E8EE',
    boxShadow: '0 8px 24px rgba(35, 38, 47, 0.045)',
  },
  Button: {
    borderRadiusMedium: '14px',
    borderRadiusSmall: '10px',
  },
  Tag: {
    borderRadius: '999px',
  },
  Input: {
    borderRadius: '14px',
    borderFocus: '1px solid #CFC3EE',
    borderHover: '1px solid #DDDFF0',
    borderFocusWarning: '1px solid #F4C96B',
    borderFocusError: '1px solid #F39AA8',
    borderHoverWarning: '1px solid #F4C96B',
    borderHoverError: '1px solid #F39AA8',
    color: '#FFFFFF',
  },
  Alert: {
    titleFontSize: '14px',
    colorWarning: '#FFF8E8',
    colorError: '#FDF0F3',
    colorInfo: '#F7F4FE',
    borderWarning: '1px solid #F4C96B',
    borderError: '1px solid #F2BCC8',
    iconColorWarning: '#D2A43C',
    iconColorError: '#E17F91',
  },
  Empty: {
    iconColor: '#A78BFA',
    textColor: '#8A8F9D',
  },
  Spin: {
    textColor: '#A78BFA',
  },
  Skeleton: {
    color: '#F1F2F7',
    colorEnd: '#E7E8EE',
  },
}

onMounted(() => {
  if (route.query.login === 'required') {
    authModal.value?.openLogin()
  }
})
</script>

<style>
.app-bg {
  min-height: calc(100vh - 64px);
  background: linear-gradient(180deg, #f7f8fc 0%, #f3f4f8 100%);
}
</style>
