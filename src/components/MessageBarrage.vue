<script setup>
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { createClient } from "@supabase/supabase-js";

// 1. Supabase 配置
const SUPABASE_URL = "https://qqrueinnfqmccfwiqczw.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_3PP6lvPA8MWhZFpdac3O4w_eWtwDlF0";
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 2. 响应式数据
const nickname = ref("");
const messageContent = ref("");
const messages = ref([]);
const isSending = ref(false);
const showError = ref("");
const barrageList = ref([]); //弹幕列表
let barrageTimer = null;

// 3. 格式化时间 —— 和日记代码完全一致（核心修复）
const formatTime = (dateStr) => {
  if (!dateStr) return "无";

  // 核心修复：如果时间字符串不包含 '+' 或 'Z'，说明是纯 timestamp，需要手动处理偏移
  let d = new Date(dateStr);

  // 如果数据库存的是 UTC 且没带标识，我们要手动补上那 8 小时的毫秒数
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

// 4. 获取留言
const fetchMessages = async () => {
  try {
    const { data, error } = await supabase
      .from("messages")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) throw error;
    messages.value = data.map((item) => ({
      ...item,
      formattedTime: formatTime(item.created_at),
    }));
    initBarrage();
    // 初始化弹幕
    // catch 块：捕获try里的所有错误，执行错误处理
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
    // 1. 发送数据并立即获取返回结果
    const { data, error } = await supabase
      .from("messages")
      .insert([
        {
          nickname: nickname.value.trim(),
          content: messageContent.value.trim(),
        },
      ])
      .select(); // 必须带上 .select() 才能拿到刚存进去的带 ID 和时间的数据

    if (error) throw error;

    // 2. 插队逻辑：让弹幕“秒出”
    if (data && data[0]) {
      const luckyMsg = data[0];
      const immediateItem = {
        // 使用 temp 前缀区分，防止与 Realtime 推送过来的 ID 冲突
        id: "temp-" + luckyMsg.id,
        nickname: luckyMsg.nickname,
        content: luckyMsg.content,
        time: formatTime(luckyMsg.created_at), // 确保使用了你之前的 formatTime 函数
        top: `${Math.floor(Math.random() * 80) + 10}%`,
        speed: 18, // 保持与你 initBarrage 一致的速度
        start: false,
      };

      // 直接推进显示列表，实现零延迟发射
      barrageList.value.push(immediateItem);

      // 必须在 nextTick 里改变 start，否则 CSS 动画无法触发
      nextTick(() => {
        immediateItem.start = true;
      });
    }

    // 3. 清空输入框
    messageContent.value = "";

    // --- 重要：删掉了 await fetchMessages() ---
    // 理由：Realtime 已经监听了 INSERT 事件，它会自动帮你更新 messages.value 数组
  } catch (e) {
    console.error("发送留言失败:", e.message);
    showError.value = "发送失败，请稍后重试";
  } finally {
    isSending.value = false;
  }
};

// 7. 生命周期
let messageChannel = null;

onMounted(() => {
  // 1. 依然先获取现有留言（保持原样）
  fetchMessages();

  // 2. 开启实时监听 (Realtime)
  // 注意：确保你在 Supabase 后台的 Replication 里开启了 messages 表的 Realtime 开关
  messageChannel = supabase
    .channel("public:messages") // 频道起个名字
    .on(
      "postgres_changes",
      {
        event: "INSERT", // 仅监听插入操作
        schema: "public",
        table: "messages",
      },
      (payload) => {
        // payload.new 就是数据库刚存入的那条新数据
        console.log("实时收到新消息:", payload.new);

        // 核心修复：手动处理时区并格式化
        const newMessage = {
          ...payload.new,
          formattedTime: formatTime(payload.new.created_at),
        };

        // 将新消息塞进数组最前面（这样页面和弹幕就能感应到变化）
        messages.value.unshift(newMessage);

        // 可选：如果希望发完立即出弹幕而不等计时器，可以在这里微调 initBarrage
      }
    )
    .subscribe();
});

onUnmounted(() => {
  // 1. 清除弹幕定时器（保持原样）
  if (barrageTimer) clearInterval(barrageTimer);

  // 2. 断开实时连接（非常重要，否则会消耗连接数并导致内存泄漏）
  if (messageChannel) {
    supabase.removeChannel(messageChannel);
  }
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