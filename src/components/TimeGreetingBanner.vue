<template>
  <div
    class="greeting-banner"
    :style="{ backgroundImage: `url(${currentBgImage})` }"
  >
    <div class="greeting-overlay">
      <h1 class="greeting-text">{{ currentGreeting }}</h1>
      <p class="greeting-subtext">这是Zero的个人小站，留下你的足迹吧✨</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";

// ========== 1. 配置：背景图路径（替换成你项目里的实际路径） ==========

// ========== 2. 时间问候逻辑（完全按你给的时间段） ==========
const getGreeting = () => {
  const now = new Date();
  const hour = now.getHours();

  // 时间段完全匹配你的要求
  if (hour >= 5 && hour < 7) return "早安";
  if (hour >= 7 && hour < 11) return "早上好";
  if (hour >= 11 && hour < 13) return "中午好";
  if (hour >= 13 && hour < 17) return "下午好";
  if (hour >= 17 && hour < 19) return "傍晚好";
  if (hour >= 19 && hour < 23) return "晚上好";
  if (hour >= 23 || hour < 1) return "晚安";
  // 1点到5点：夜深了，睡觉吧
  return "夜深了，睡觉吧";
};

// ========== 4. 实时更新（每分钟刷新一次问候/背景） ==========
const currentGreeting = ref(getGreeting());
let timer = null;

const updateGreeting = () => {
  currentGreeting.value = getGreeting();
};

onMounted(() => {
  // 页面加载时立即更新
  updateGreeting();
  // 每分钟刷新一次，保证时间变化时自动切换
  timer = setInterval(updateGreeting, 60 * 1000);
});

onUnmounted(() => {
  // 组件销毁时清除定时器，避免内存泄漏
  clearInterval(timer);
});
</script>

<style scoped>
/* 组件容器：全屏宽度，适配弹幕区上方 */
.greeting-banner {
  width: 100%;
  height: 240px; /* 高度可按需调整 */
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  /* margin-bottom: 20px; */
  /* box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); */
}

/* 半透明遮罩：让文字更清晰，不抢背景风头 */
.greeting-overlay {
  width: 100%;
  height: 100%;
  /* background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.2),
    rgba(0, 0, 0, 0.5)
  ); */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* backdrop-filter: blur(2px); */
}

/* 主问候语样式：和你网站风格统一的淡蓝色发光 */
.greeting-text {
  font-size: 72px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 4px;
  margin: 0 0 12px 0;
  text-shadow: 0 0 12px rgba(184, 224, 255, 0.8),
    0 0 24px rgba(184, 224, 255, 0.5);
  animation: glow 3s ease-in-out infinite alternate;
}

/* 副标题样式 */
.greeting-subtext {
  font-size: 22px;
  color: #b8e0ff;
  opacity: 0.9;
  letter-spacing: 2px;
  margin: 0;
}

/* 呼吸发光动画：提升氛围感 */
@keyframes glow {
  0% {
    opacity: 0.85;
    text-shadow: 0 0 10px rgba(184, 224, 255, 0.6);
  }
  100% {
    opacity: 1;
    text-shadow: 0 0 18px rgba(184, 224, 255, 0.9),
      0 0 36px rgba(184, 224, 255, 0.6);
  }
}

/* 响应式适配：移动端自动缩小 */
@media (max-width: 768px) {
  .greeting-banner {
    height: 200px;
  }
  .greeting-text {
    font-size: 24px;
    letter-spacing: 2px;
  }
  .greeting-subtext {
    font-size: 14px;
  }
}
</style>