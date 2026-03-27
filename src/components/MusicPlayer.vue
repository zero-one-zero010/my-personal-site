<script setup>
import { ref, computed, watch } from "vue";
import { Play, Pause, SkipBack, SkipForward } from "lucide-vue-next";

// 核心状态（完全保留你的逻辑）
const isPlaying = ref(false);
const audio = ref(null);
const currentTime = ref(0); // 当前播放时间
const duration = ref(0); // 总时长
const progress = ref(0); // 进度条百分比

// 歌词数据（保留你的示例）
const lyrics = ref([
  { time: 0, text: "「 今日 BGM - 轻音乐 」" },
  { time: 10, text: "风轻轻吹过，云慢慢飘过" },
  { time: 20, text: "享受此刻的宁静与美好" },
  { time: 30, text: "生活需要一些温柔的旋律" },
  { time: 40, text: "愿你被温柔以待" },
  { time: 50, text: "心有山海，静而无忧" },
  { time: 60, text: "温柔且坚定，知足且上进" },
  { time: 70, text: "追风赶月，不负韶华" },
  { time: 80, text: "心有旷野，目有繁星" },
  { time: 90, text: "且停且忘且随风" },
  { time: 100, text: "向旷野奔跑，使故事发生" },
  { time: 110, text: "行走世间，收集落日与风" },
  { time: 120, text: "—— 010音乐" },
]);
const currentLyric = ref(lyrics.value[0].text); // 当前显示的歌词

// 播放/暂停切换（保留）
const togglePlay = () => {
  isPlaying.value = !isPlaying.value;
  if (isPlaying.value) {
    audio.value.play();
  } else {
    audio.value.pause();
  }
};

// 格式化时间（保留）
const formatTime = (seconds) => {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${min}:${sec < 10 ? "0" + sec : sec}`;
};

// 进度条点击跳转（保留）
const handleProgressClick = (e) => {
  const rect = e.target.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const percent = clickX / rect.width;
  progress.value = percent * 100;
  audio.value.currentTime = percent * duration.value;
};

// 监听音频时间更新（保留）
watch(audio, (el) => {
  if (!el) return;
  // 实时更新进度
  el.ontimeupdate = () => {
    currentTime.value = el.currentTime;
    progress.value = (el.currentTime / el.duration) * 100;

    // 匹配歌词
    for (let i = lyrics.value.length - 1; i >= 0; i--) {
      if (el.currentTime >= lyrics.value[i].time) {
        currentLyric.value = lyrics.value[i].text;
        break;
      }
    }
  };
  // 获取总时长
  el.onloadedmetadata = () => {
    duration.value = el.duration;
  };
});

// 计算属性（保留）
const formattedCurrentTime = computed(() => formatTime(currentTime.value));
const formattedDuration = computed(() => formatTime(duration.value));
</script>

<template>
  <!-- 改造核心：竖向长方形容器 -->
  <div class="netease-player">
    <!-- 1. 居中专辑封面（放大+居中） -->
    <div class="cover-wrapper" :class="{ spinning: isPlaying }">
      <img
        class="album-cover"
        src="/51650f186e1ca5baeb2ed288f98800d2.png"
        alt="专辑封面"
      />
    </div>

    <!-- 2. 歌词展示（居中） -->
    <div class="lyrics-container">
      <p class="current-lyric">{{ currentLyric }}</p>
    </div>

    <!-- 3. 进度条区域（宽度铺满） -->
    <div class="progress-area">
      <div class="time-info">
        <span>{{ formattedCurrentTime }}</span>
        <span>{{ formattedDuration }}</span>
      </div>
      <div class="progress-bar" @click="handleProgressClick">
        <div class="progress-fill" :style="{ width: `${progress}%` }">
          <div class="progress-dot" :style="{ left: `${progress}%` }"></div>
        </div>
      </div>
    </div>

    <!-- 4. 控制按钮（居中） -->
    <div class="control-buttons">
      <SkipBack size="20" color="#ccc" class="control-btn" />
      <div class="play-btn" @click="togglePlay">
        <component :is="isPlaying ? Pause : Play" size="32" color="white" />
      </div>
      <SkipForward size="20" color="#ccc" class="control-btn" />
    </div>

    <!-- 音频源（保留） -->
    <audio ref="audio" loop src="/IsotlanD - The World Is Asleep.mp3"></audio>
  </div>
</template>

<style scoped>
/* 改造核心：竖向长方形容器（适配父容器100%宽高） */
.netease-player {
  /* 关键：竖向布局 + 100%宽高适配父容器 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-around; /* 均匀分布各区域 */
  gap: 15px;
  background: rgba(24, 24, 24, 0.5); /* 0.3是透明度，0-1之间调整 */
  backdrop-filter: blur(8px);
  padding: 25px 20px;
  border-radius: 12px;
  width: 100%; /* 铺满父容器宽度 */
  height: 100%; /* 铺满父容器高度 */
  box-sizing: border-box;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* 1. 专辑封面（放大+居中） */
.cover-wrapper {
  width: 180px; /* 放大封面 */
  height: 180px;
  border-radius: 90px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(187, 230, 254, 0.5);
  transition: all 0.3s ease;
}

.album-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 旋转动画（保留） */
.spinning {
  animation: rotate 8s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 2. 歌词区域（居中+放大字体） */
.lyrics-container {
  color: #fff;
  width: 100%;
  text-align: center;
}

.current-lyric {
  font-size: 18px; /* 放大歌词字体 */
  margin: 0;
  color: #f5f5f5;
  line-height: 1.8;
  letter-spacing: 0.8px;
}

/* 3. 进度条区域（宽度铺满） */
.progress-area {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%; /* 铺满容器宽度 */
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #ccc;
}

/* 进度条样式（完全保留） */
.progress-bar {
  width: 100%;
  height: 4px;
  background: #444;
  border-radius: 2px;
  cursor: pointer;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: rgb(190, 232, 255);
  border-radius: 2px;
  transition: width 0.1s ease;
}

.progress-dot {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: rgb(190, 232, 255);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.progress-bar:hover .progress-dot {
  opacity: 1;
}

/* 4. 控制按钮（居中排列） */
.control-buttons {
  display: flex;
  align-items: center;
  gap: 25px; /* 加大按钮间距 */
}

.control-btn {
  cursor: pointer;
  transition: color 0.2s ease;
}

.control-btn:hover {
  color: rgb(190, 232, 255);
}

/* 播放按钮（保留原有样式） */
.play-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgb(190, 232, 255);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.play-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px rgba(190, 232, 255, 0.6);
}
</style>