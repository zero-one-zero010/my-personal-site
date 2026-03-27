<script setup>
import { ref, onMounted, onUnmounted } from "vue";

// 响应式存储当前时间
const currentTime = ref(new Date());
// 用 ref 包装 new Date()，变成响应式时间对象，只要它的值变了，页面上显示的时间就会自动更新
let timeInterval = null;

// 更新时间函数，每次调用这个函数，currentTime 就会变成 “此时此刻” 的系统时间
const updateTime = () => {
  currentTime.value = new Date();
};

// 格式化时分秒（24小时制，两位数显示）
const formatTime = (date) => {
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
};

// 格式化日期（年-月-日 星期）
const formatDate = (date) => {
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });
};

// 组件挂载时启动定时器
onMounted(() => {
  // 立即更新一次时间
  updateTime();
  // 每秒更新时间 设置定时器
  timeInterval = setInterval(updateTime, 1000);
});

// 组件卸载时清除定时器（防止内存泄漏）
onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval);
  }
});
</script>

<template>
  <div class="clock-container">
    <!-- 数字时钟（大号字体） -->
    <div class="clock-time">{{ formatTime(currentTime) }}</div>
    <!-- 日期显示（小号字体） -->
    <div class="clock-date">{{ formatDate(currentTime) }}</div>
  </div>
</template>

<style scoped>
.clock-container {
  /* 适配播放器区域的样式，可根据需要调整 */
  background: rgba(24, 24, 24, 0.5);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  color: white;
  font-family: "Microsoft YaHei", sans-serif;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  width: 100%;
  box-sizing: border-box;
}

/* 时间数字样式 */
.clock-time {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
  letter-spacing: 2px;
  /* 文字发光效果，增强视觉 */
  text-shadow: 0 0 10px rgba(190, 232, 255, 0.7);
}

/* 日期文字样式 */
.clock-date {
  font-size: 16px;
  opacity: 0.8;
  letter-spacing: 1px;
}

/* 响应式适配（可选）适配手机端 */
@media (max-width: 768px) {
  .clock-time {
    font-size: 28px;
  }
  .clock-date {
    font-size: 14px;
  }
}
</style>