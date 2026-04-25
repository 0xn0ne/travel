<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goToJ() {
  router.push('/j')
}

function goToP() {
  router.push('/p')
}
</script>

<template>
  <div class="entry-view">
    <div class="entry-center">
      <div class="entry-bg">
        <div class="entry-brand">拾途</div>
        <div class="entry-sub">选择你喜欢的旅行方式，开始吧</div>
        <div class="entry-cards">
          <div class="entry-card" @click="goToJ">
            <div class="entry-card-icon">📋</div>
            <div class="entry-card-title">计划狂魔J人</div>
            <div class="entry-card-desc">精细规划，掌控每一天的行程</div>
          </div>
          <div class="entry-card entry-card-p" @click="goToP">
            <div class="entry-card-icon">✨</div>
            <div class="entry-card-title">即兴玩家P人</div>
            <div class="entry-card-desc">随性出发，让旅程自由生长</div>
          </div>
        </div>
      </div>
    </div>
    <img
      class="entry-deco"
      src="/imgs/176471776829509__副本.pic-removebg-preview.png"
      alt=""
    />
  </div>
</template>

<style scoped>
.entry-view {
  height: calc(100vh - 64px);
  position: relative;
  background-color: var(--bg-main);
  background-image:
    radial-gradient(rgba(158, 190, 219, 0.1) 1px, transparent 1px),
    radial-gradient(rgba(255, 255, 255, 0.65) 1px, transparent 1px);
  background-position: 0 0, 14px 14px;
  background-size: 26px 26px, 26px 26px;
}

.entry-center {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translateY(-100px);
}

.entry-bg {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  position: relative;
}

.entry-brand {
  font-family: 'ZCoolHappy', sans-serif;
  font-size: 60px;
  font-weight: 400;
  color: var(--type-title);
  letter-spacing: 0.08em;
}

.entry-sub {
  font-family: 'ZCoolHappy', sans-serif;
  font-size: 22px;
  color: var(--type-muted);
  margin-top: -8px;
}

.entry-cards {
  display: flex;
  gap: 24px;
  margin-top: 16px;
}

.entry-card {
  width: 340px;
  padding: 52px 44px;
  background: rgba(255, 255, 255, 0.90);
  border: none;
  border-radius: 28px;
  backdrop-filter: blur(12px);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.entry-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px rgba(108, 140, 213, 0.15);
}

.entry-card-p {
  cursor: default;
}

.entry-card-icon {
  font-size: 56px;
  line-height: 1;
}

.entry-card-title {
  font-family: 'ZCoolHappy', sans-serif;
  font-size: 26px;
  font-weight: 400;
  color: var(--type-title);
}

.entry-card-desc {
  font-family: 'ZCoolHappy', sans-serif;
  font-size: 16px;
  color: var(--type-muted);
  line-height: 1.6;
}

.entry-deco {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 300px;
  height: auto;
  object-fit: contain;
  pointer-events: none;
  opacity: 0.8;
}
</style>
