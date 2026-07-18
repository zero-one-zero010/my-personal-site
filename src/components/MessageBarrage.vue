<script setup>
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { api } from "../api";

const nickname = ref("");
const messageContent = ref("");
const messages = ref([]);
const isSending = ref(false);
const showError = ref("");
const barrageList = ref([]);
let barrageTimer = null;

const formatTime = (dateStr) => {
  if (!dateStr) return "无";

  let d = new Date(dateStr);

  if (!dateStr.includes("+") && !dateStr.toLowerCase().includes("z")) {
    d = new Date(d.getTime() + 8 * 60 * 60 * 1000);
  }

  return `${d.getFullYear()}-${(d.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d
    .getHours()
    .toString()
    .padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
};

const fetchMessages = async () => {
  try {
    const data = await api.getMessages();
    messages.value = data.map((item) => ({
      ...item,
      formattedTime: formatTime(item.created_at),
    }));
    initBarrage();
  } catch (e) {
    console.error("获取留言失败:", e.message);
    showError.value = "加载留言失败，请稍后重试";
  }
};

// 5. 初始化弹幕（固定速度/频率，逻辑不变）
const initBarrage = () => {
  // 1. 如果定时器已存在则不重复初始化，防止发送新消息时开启多个定时器
  if (barrageTimer) return;

  // 原有配置保持不变
  const FIXED_SPEED = 24;
  const FIXED_INTERVAL = 2500;

  // 2. 移除原有的 barrageList.value = []，确保旧弹幕不消失
  let index = 0;

  barrageTimer = setInterval(() => {
    // 3. 动态检查最新的消息列表长度
    if (messages.value.length === 0) return;

    // 如果播到了最后一条，重置索引实现循环
    if (index >= messages.value.length) {
      index = 0;
    }

    // 4. 直接从最新的 messages.value 中取数据
    const msg = messages.value[index];

    // 创建弹幕对象（使用随机 ID 或时间戳防止 Key 重复）
    const item = {
      id: Date.now() + Math.random(), // 避免 Realtime 插入时 id 冲突导致 DOM 抖动
      nickname: msg.nickname,
      content: msg.content,
      time: msg.formattedTime,
      top: `${Math.floor(Math.random() * 80) + 10}%`,
      speed: FIXED_SPEED,
      start: false,
    };

    // 5. 追加而不是重置
    barrageList.value.push(item);

    nextTick(() => {
      item.start = true;
    });

    index++;

    // 6. 性能维护：当数组过长时，悄悄移除已经飞出屏幕的旧弹幕数据
    if (barrageList.value.length > 30) {
      barrageList.value.shift();
    }
  }, FIXED_INTERVAL);
};

// 6. 发送留言（逻辑不变，Supabase自动生成UTC时间）
// 页面初始化时，messages 从数据库获取所有旧消息 → 定时器每 2.5 秒从 messages 取一条，
// push 到 barrageList → Vue 渲染 DOM，弹幕按 2.5 秒间隔出现，所以是加了一层
const sendMessage = async () => {
  if (!nickname.value.trim()) {
    showError.value = "昵称不能为空！";
    return;
  }
  if (!messageContent.value.trim()) {
    showError.value = "留言内容不能为空！";
    return;
  }

  showError.value = "";
  isSending.value = true;

  try {
    const luckyMsg = await api.createMessage(
      nickname.value.trim(),
      messageContent.value.trim()
    );

    const formatted = {
      ...luckyMsg,
      formattedTime: formatTime(luckyMsg.created_at),
    };
    messages.value.unshift(formatted);

    const immediateItem = {
      id: "temp-" + luckyMsg.id,
      nickname: luckyMsg.nickname,
      content: luckyMsg.content,
      time: formatted.formattedTime,
      top: `${Math.floor(Math.random() * 80) + 10}%`,
      speed: 18,
      start: false,
    };

    barrageList.value.push(immediateItem);
    nextTick(() => {
      immediateItem.start = true;
    });

    messageContent.value = "";
  } catch (e) {
    console.error("发送留言失败:", e.message);
    showError.value = "发送失败，请稍后重试";
  } finally {
    isSending.value = false;
  }
};

onMounted(() => {
  fetchMessages();
});

onUnmounted(() => {
  if (barrageTimer) clearInterval(barrageTimer);
});
</script>

<template>
  <div class="message-barrage-container">
    <div class="barrage-view">
      <div class="barrage-mask-left"></div>
      <div
        class="barrage-item"
        v-for="item in barrageList"
        :key="item.id"
        :style="{
          top: item.top,
          transition: `transform ${item.speed}s linear`,
          transform: item.start ? 'translateX(-800%)' : 'translateX(0)',
          opacity: 1,
        }"
      >
        <!-- “平滑移动” 的关键：告诉浏览器，当 transform 属性变化时，
       用匀速（linear）、指定时长（item.speed 秒）** 的过渡动画来执行 -->
        <span class="barrage-nickname">{{ item.nickname }}：</span>
        <span class="barrage-content">{{ item.content }}</span>
        <span class="barrage-time">{{ item.time }}</span>
      </div>
    </div>

    <div class="error-tip" v-if="showError">{{ showError }}</div>

    <div class="message-input-area">
      <input
        type="text"
        v-model="nickname"
        placeholder="请输入你的昵称（必填）"
        class="nickname-input"
        :class="{ error: !nickname.trim() && showError.includes('昵称') }"
      />
      <textarea
        v-model="messageContent"
        placeholder="请输入留言内容..."
        class="content-input"
        :class="{ error: !messageContent.trim() && showError.includes('内容') }"
      ></textarea>
      <button class="send-btn" @click="sendMessage" :disabled="isSending">
        {{ isSending ? "发送中..." : "发送" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 所有样式完全不变 */
.message-barrage-container {
  width: 100%;
  border-radius: 12px;
  padding: 15px;
  box-sizing: border-box;
  color: #fff;
  margin-top: 40px;
  margin-bottom: 20px;
}

.barrage-view {
  width: 100%;
  height: 500px;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
  /* 超出部分直接隐藏，所以弹幕逐字消失 */
  margin-bottom: 15px;
}

.barrage-item {
  position: absolute;
  white-space: nowrap;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 20px;
  font-size: 14px;
  color: #fff;
  z-index: 1;
  left: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
}

.barrage-nickname {
  color: #b8e0ff;
  font-weight: 600;
}

.barrage-content {
  color: #fff;
}

.barrage-time {
  color: #cccccc;
  font-size: 12px;
  opacity: 0.8;
}

.message-input-area {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 100%;
}

.nickname-input {
  width: 150px;
  padding: 10px 12px;
  border: 2px solid rgb(190, 232, 255);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 14px;
  outline: none;
}

.nickname-input::placeholder {
  color: #999;
}

.nickname-input.error {
  border-color: #ff4444;
}

.content-input {
  flex: 1;
  height: 20px;
  padding: 10px 12px;
  border: 2px solid #ccc;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 14px;
  resize: none;
  outline: none;
}

.content-input::placeholder {
  color: #999;
}

.content-input.error {
  border-color: #ff4444;
}

.send-btn {
  width: 80px;
  height: 40px;
  border: none;
  border-radius: 6px;
  background: rgb(190, 232, 255);
  color: #000;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
}

.send-btn:disabled {
  background: #999;
  cursor: not-allowed;
  opacity: 0.7;
}

.send-btn:hover:not(:disabled) {
  background: rgb(150, 210, 255);
  transform: scale(1.02);
}

.error-tip {
  color: #ff4444;
  font-size: 12px;
  margin-bottom: 10px;
  text-align: center;
}

@media (max-width: 768px) {
  .message-input-area {
    flex-direction: column;
    align-items: stretch;
  }

  .nickname-input {
    width: 100%;
  }

  .send-btn {
    width: 100%;
    height: 40px;
  }

  .content-input {
    height: 80px;
  }

  .barrage-view {
    height: 150px;
  }
}
</style>