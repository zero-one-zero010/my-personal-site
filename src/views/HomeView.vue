<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { api } from "../api";
import WeatherCard from "../components/WeatherCard.vue";
import MusicPlayer from "../components/MusicPlayer.vue";
import Clock from "../components/Clock.vue";
import Diary from "../components/Diary.vue";
import AiChat from "../components/AiChat.vue";
import ProfileSection from "../components/ProfileSection.vue";
import MessageBarrage from "../components/MessageBarrage.vue";
import TimeGreetingBanner from "../components/TimeGreetingBanner.vue";

// 城市数据（保留）
const cities = ref([
  {
    name: "北京",
    center: [116.4, 39.9],
    color: "rgba(254, 229, 174, 0.9)",
    temp: "--",
    sunrise: "--",
    sunset: "--",
  },
  {
    name: "广州",
    center: [113.2, 23.1],
    color: "rgba(87, 130, 165, 0.75)",
    temp: "--",
    sunrise: "--",
    sunset: "--",
  },
  {
    name: "杭州",
    center: [120.15, 30.28],
    color: "rgba(180, 70, 75, 0.5)",
    temp: "--",
    sunrise: "--",
    sunset: "--",
  },
  {
    name: "深圳",
    center: [114.0, 22.5],
    color: "rgba(150, 162, 162, 0.75)",
    temp: "--",
    sunrise: "--",
    sunset: "--",
  },
]);

// ========== 新增：背景图切换相关 ==========
// 1. 定义响应式背景图变量（替换夜晚背景图路径）
const bgImage = ref("/842f0d17a4a59407ca2c14f7cbb5978c3816626.jpg"); // 白天背景
const dayBgUrl = "/842f0d17a4a59407ca2c14f7cbb5978c3816626.jpg"; // 白天背景（和上面一致）
const nightBgUrl = "/00099c624c757bf8fed01fb39bbb0002f24102bb.jpg"; // 👉 替换成你的夜晚背景图URL

// 2. 时间判断 + 切换背景核心函数
const checkTimeAndSwitchBg = () => {
  const now = new Date();
  const hours = now.getHours(); // 获取当前小时（0-23）
  // 逻辑：晚7点（19）及以后 或 早6点以前 → 夜晚背景；否则白天背景
  bgImage.value = hours >= 19 || hours < 6 ? nightBgUrl : dayBgUrl;
};

// 3. 定时器变量（用于销毁组件时清除）
let bgTimer = null;

let map = null;

const fetchWeather = async () => {
  try {
    const data = await api.getFootprints();
    data.forEach((item) => {
      const city = cities.value.find((c) => c.name === item.name);
      if (city) {
        city.temp = item.temp || "--";
        city.sunrise = item.sunrise || "--";
        city.sunset = item.sunset || "--";
      }
    });
  } catch (e) {
    console.error("获取天气数据失败:", e.message);
  }
};

// 地图初始化（保留 + 新增背景图初始化）
onMounted(() => {
  // 初始化背景图（页面加载时先判断一次）
  checkTimeAndSwitchBg();
  // 每分钟检查一次时间，确保到点切换
  bgTimer = setInterval(checkTimeAndSwitchBg, 60000);

  // 原有地图逻辑
  map = new AMap.Map("map", {
    center: [105, 35],
    zoom: 4,
    theme: "amap://styles/dark",
    resizeEnable: true,
  });
  fetchWeather();
  cities.value.forEach((c) => {
    new AMap.CircleMarker({
      center: c.center,
      radius: 6,
      fillColor: c.color,
      strokeColor: "white",
      strokeWeight: 2,
      fillOpacity: 0.9,
    }).setMap(map);
  });
  map.resize();
});

// 新增：组件销毁时清除定时器（避免内存泄漏）
onUnmounted(() => {
  if (bgTimer) clearInterval(bgTimer);
});

const fly = (c) => map && map.setZoomAndCenter(10, c.center);
</script>

<template>
  <!-- 最外层：绑定响应式背景图 + 原有样式 -->
  <div
    :style="`
      background: url(${bgImage}) no-repeat center center fixed;
      background-size: cover;
      min-height: 100vh;
      padding: 20px;
      box-sizing: border-box;
      margin: 0;
      display: flex;
      flex-direction: column; /* 改为纵向布局，方便置顶组件 */
      align-items: center;
      gap: 20px; /* 置顶组件和大框之间的间距 */
    `"
  >
    <TimeGreetingBanner />
    <div style="width: 95%; max-width: 1400px">
      <MessageBarrage />
    </div>
    <!-- 核心：单个半透明大框包裹所有组件（原有样式不变） -->
    <div
      style="
        width: 95%; /* 大框宽度（可改1200px固定宽度） */
        max-width: 1400px; /* 最大宽度，避免太宽 */
        background: rgba(0, 0, 0, 0.4); /* 整体半透明背景 */
        border-radius: 16px; /* 大框圆角 */
        padding: 25px; /* 大框内边距 */
        display: flex;
        flex-direction: column;
        gap: 25px; /* 内部组件之间的间距 */
        box-sizing: border-box;
      "
    >
      <ProfileSection />
      <!-- 1. 天气卡片（内部布局不变） -->
      <div
        style="
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 15px;
          margin-bottom: 20px;
        "
      >
        <!-- 添加事件 点击飞到指定地点 -->
        <WeatherCard
          v-for="c in cities"
          :key="c.name"
          :city="c"
          @click="fly(c)"
          style="cursor: pointer"
        />
      </div>

      <!-- 2. 播放器+地图（内部左右布局+等高不变） -->
      <div style="display: flex; gap: 25px; flex: 1; min-height: 500px">
        <!-- 左侧播放器 -->
        <div
          style="
            width: 400px;
            flex-shrink: 0;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 20px;
          "
        >
          <!-- 时钟组件（固定高度，或者自适应） -->
          <Clock style="flex-shrink: 0" />

          <!-- 播放器组件（自动占满剩余高度） -->
          <div style="flex: 1; min-height: 0">
            <MusicPlayer style="width: 100%; height: 100%" />
          </div>
        </div>

        <!-- 右侧缩小的地图 -->
        <div
          id="map"
          style="
            flex: 1;
            width: 800px !important;
            height: 100% !important;
            min-height: 500px;
            border-radius: 8px;
            overflow: hidden;
          "
        ></div>
      </div>
      <Diary />
      <AiChat />
    </div>
  </div>
</template>

<style scoped>
/* 适配播放器尺寸 */
:deep(.netease-player) {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}
</style>