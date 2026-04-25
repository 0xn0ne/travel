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
    primaryColor: '#6C8CD5',
    primaryColorHover: '#7B99DC',
    primaryColorPressed: '#5D7EC9',
    primaryColorSuppl: '#6C8CD5',
    successColor: '#76C893',
    successColorHover: '#8FD8A7',
    successColorPressed: '#5FB17C',
    warningColor: '#FFD8A8',
    warningColorHover: '#FFE1B9',
    warningColorPressed: '#F2C48D',
    errorColor: '#F39AA8',
    errorColorHover: '#F7B2BD',
    errorColorPressed: '#E17F91',
    textColorBase: '#2F4F6F',
    textColor1: '#2F4F6F',
    textColor2: '#5B6B7B',
    textColor3: '#8EA2B5',
    bodyColor: '#EAF3F8',
    cardColor: '#FFFFFF',
    modalColor: '#FFFFFF',
    popoverColor: '#FFFFFF',
    tableColor: '#F0F8FF',
    inputColor: '#FFFFFF',
    actionColor: '#F0F8FF',
    borderColor: '#1D4271',
    dividerColor: '#C5DEFF',
    borderRadius: '22px',
    borderRadiusSmall: '12px',
    fontFamily: "'ZCoolHappy', sans-serif",
    fontFamilyMono: "'ZCoolHappy', sans-serif",
  },
  Card: {
    borderRadius: '22px',
    color: '#FFFFFF',
    borderColor: '#1D4271',
    boxShadow: 'none',
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
    borderFocus: '2px solid #6C8CD5',
    borderHover: '2px solid #1D4271',
    color: '#FFFFFF',
  },
  Alert: {
    titleFontSize: '14px',
    colorWarning: '#FFF8E8',
    colorError: '#FDF0F3',
    colorInfo: '#F0F8FF',
    borderWarning: '2px solid #FFD166',
    borderError: '2px solid #F39AA8',
    iconColorWarning: '#D2A43C',
    iconColorError: '#E17F91',
  },
  Empty: {
    iconColor: '#9D94FF',
    textColor: '#6F86A6',
  },
  Spin: {
    textColor: '#9D94FF',
  },
  Skeleton: {
    color: '#D6EAFF',
    colorEnd: '#EAF4FF',
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
  background: #D5EBFA;
  font-family: var(--font-ui-rounded);
}
</style>
