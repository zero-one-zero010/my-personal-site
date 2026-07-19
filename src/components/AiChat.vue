<script setup>
import { nextTick, onMounted, onUnmounted, ref } from "vue";
import { api } from "../api";

/** 打字机：间隔越大越慢；每次吐出字符数 */
const TYPE_INTERVAL_MS = 45;
const CHARS_PER_TICK = 1;

const messages = ref([]);
const inputText = ref("");
const isSending = ref(false);
const isLoading = ref(false);
const errorTip = ref("");
const listRef = ref(null);

let typeQueue = [];
let typingTimer = null;

const scrollToBottom = async () => {
  await nextTick();
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight;
  }
};

const stopTyping = () => {
  if (typingTimer) {
    clearInterval(typingTimer);
    typingTimer = null;
  }
};

const flushTyping = (assistantIndex) => {
  const msg = messages.value[assistantIndex];
  if (!msg || typeQueue.length === 0) return;

  const take = typeQueue.splice(0, CHARS_PER_TICK).join("");
  msg.content += take;
  msg.streaming = true;
  scrollToBottom();
};

const startTyping = (assistantIndex) => {
  if (typingTimer) return;
  typingTimer = setInterval(() => {
    if (typeQueue.length === 0) {
      stopTyping();
      return;
    }
    flushTyping(assistantIndex);
  }, TYPE_INTERVAL_MS);
};

const waitQueueEmpty = () =>
  new Promise((resolve) => {
    const check = () => {
      if (typeQueue.length > 0) {
        if (!typingTimer) startTyping(assistantIndexRef);
        setTimeout(check, 30);
        return;
      }
      // 队列已空：再等一拍，让最后一次 interval 清掉
      if (typingTimer) {
        setTimeout(check, TYPE_INTERVAL_MS);
        return;
      }
      resolve();
    };
    check();
  });

let assistantIndexRef = -1;

const loadHistory = async () => {
  isLoading.value = true;
  errorTip.value = "";
  try {
    const data = await api.getChatHistory();
    messages.value = (data || []).map((item) => ({
      id: item.id,
      role: item.role,
      content: item.content,
    }));
    await scrollToBottom();
  } catch (e) {
    console.error("加载聊天记录失败:", e);
    errorTip.value = e.message || "加载聊天记录失败";
  } finally {
    isLoading.value = false;
  }
};

const clearChat = async () => {
  if (isSending.value || messages.value.length === 0) return;
  if (!confirm("确定清空全部对话记录吗？")) return;

  errorTip.value = "";
  try {
    await api.clearChatHistory();
    stopTyping();
    typeQueue = [];
    messages.value = [];
  } catch (e) {
    console.error("清空对话失败:", e);
    errorTip.value = e.message || "清空失败";
  }
};

const sendMessage = async () => {
  const text = inputText.value.trim();
  if (!text || isSending.value) return;

  errorTip.value = "";
  messages.value.push({ role: "user", content: text });
  inputText.value = "";
  await scrollToBottom();

  messages.value.push({ role: "assistant", content: "", streaming: true });
  await scrollToBottom();

  isSending.value = true;
  const assistantIndex = messages.value.length - 1;
  assistantIndexRef = assistantIndex;
  typeQueue = [];
  stopTyping();

  try {
    await api.chatStream(text, {
      onDelta: (delta) => {
        // 按 Unicode 码点拆开，中文也能一个字一个字出
        typeQueue.push(...Array.from(delta));
        startTyping(assistantIndex);
      },
      onDone: async (data) => {
        await waitQueueEmpty();
        stopTyping();

        const msg = messages.value[assistantIndex];
        if (!msg) return;
        // 与后端最终文本对齐
        msg.content = data.content || msg.content;
        msg.id = data.id;
        msg.streaming = false;
        await scrollToBottom();
      },
    });

    const msg = messages.value[assistantIndex];
    if (msg && !msg.content) {
      msg.content = "（没有收到回复）";
      msg.streaming = false;
    }
  } catch (e) {
    console.error("AI 对话失败:", e);
    errorTip.value = e.message || "发送失败，请稍后重试";
    stopTyping();
    typeQueue = [];
    const msg = messages.value[assistantIndex];
    if (msg) {
      if (!msg.content) {
        msg.content = "抱歉，刚才没有回应成功，请稍后再试。";
      }
      msg.streaming = false;
    }
    await scrollToBottom();
  } finally {
    isSending.value = false;
  }
};

const onKeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

onMounted(() => {
  loadHistory();
});

onUnmounted(() => {
  stopTyping();
  typeQueue = [];
});
</script>

<template>
  <div class="ai-chat-section">
    <div class="ai-chat-header">
      <div>
        <div class="ai-chat-title">AI 小助手</div>
        <div class="ai-chat-subtitle">跟我聊聊吧，有什么想聊的，都可以问我</div>
      </div>
      <button
        class="clear-btn"
        type="button"
        :disabled="isSending || isLoading || messages.length === 0"
        @click="clearChat"
      >
        清空对话
      </button>
    </div>

    <div ref="listRef" class="ai-chat-messages">
      <div v-if="isLoading" class="ai-chat-empty">加载记录中…</div>
      <div v-else-if="messages.length === 0" class="ai-chat-empty">
        还没有消息。试着打个招呼吧～
      </div>
      <template v-else>
        <div
          v-for="(msg, index) in messages"
          :key="msg.id || index"
          class="ai-bubble"
          :class="msg.role === 'user' ? 'is-user' : 'is-assistant'"
        >
          <div class="ai-bubble-role">
            {{ msg.role === "user" ? "你" : "AI" }}
          </div>
          <div class="ai-bubble-content">
            <span>{{ msg.content }}</span>
            <span
              v-if="msg.streaming && !msg.content"
              class="ai-stream-placeholder"
              >思考中…</span
            >
            <span v-else-if="msg.streaming" class="ai-caret">|</span>
          </div>
        </div>
      </template>
    </div>

    <div v-if="errorTip" class="ai-error">{{ errorTip }}</div>

    <div class="ai-chat-input-row">
      <textarea
        v-model="inputText"
        class="ai-chat-input"
        rows="1"
        placeholder="输入你想说的话…（Enter 发送，Shift+Enter 换行）"
        :disabled="isSending || isLoading"
        @keydown="onKeydown"
      />
      <button
        class="send-btn"
        type="button"
        :disabled="isSending || isLoading || !inputText.trim()"
        @click="sendMessage"
      >
        {{ isSending ? "生成中..." : "发送" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-section {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 16px;
  padding: 25px;
  box-sizing: border-box;
  color: #fff;
  font-family: "Microsoft YaHei", sans-serif;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ai-chat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.ai-chat-title {
  font-size: 20px;
  font-weight: bold;
  color: rgb(190, 232, 255);
}

.ai-chat-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #999;
}

.clear-btn {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  color: #ccc;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  transition: all 0.2s;
}

.clear-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-chat-messages {
  min-height: 400px;
  max-height: 520px;
  overflow-y: auto;
  background: rgba(24, 24, 24, 0.2);
  backdrop-filter: blur(2px);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: rgba(190, 232, 255, 0.35) transparent;
}

.ai-chat-messages::-webkit-scrollbar {
  width: 6px;
}

.ai-chat-messages::-webkit-scrollbar-track {
  background: transparent;
  margin: 8px 0;
}

.ai-chat-messages::-webkit-scrollbar-thumb {
  background: rgba(190, 232, 255, 0.35);
  border-radius: 999px;
}

.ai-chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(190, 232, 255, 0.55);
}

.ai-chat-empty {
  margin: auto;
  color: #999;
  font-size: 14px;
}

.ai-bubble {
  max-width: min(72%, 640px);
  width: fit-content;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-sizing: border-box;
}

.ai-bubble.is-user {
  align-self: flex-end;
  align-items: flex-end;
}

.ai-bubble.is-assistant {
  align-self: flex-start;
  align-items: flex-start;
}

.ai-bubble-role {
  font-size: 12px;
  color: #999;
}

.ai-bubble.is-user .ai-bubble-role {
  color: rgb(190, 232, 255);
}

.ai-bubble-content {
  max-width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  box-sizing: border-box;
}

.ai-bubble.is-user .ai-bubble-content {
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.ai-bubble.is-assistant .ai-bubble-content {
  background: rgba(190, 232, 255, 0.12);
  border: 1px solid rgba(190, 232, 255, 0.35);
}

.ai-stream-placeholder {
  color: #999;
  font-size: 13px;
}

.ai-caret {
  display: inline-block;
  margin-left: 1px;
  color: rgb(190, 232, 255);
  animation: ai-blink 1s step-end infinite;
}

@keyframes ai-blink {
  50% {
    opacity: 0;
  }
}

.ai-error {
  color: #ff6b6b;
  font-size: 13px;
}

.ai-chat-input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.ai-chat-input {
  flex: 1;
  min-height: 34px;
  resize: vertical;
  padding: 10px 12px;
  border: 2px solid rgb(190, 232, 255);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.1);
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}

.ai-chat-input::placeholder {
  color: #888;
}

.ai-chat-input:disabled {
  opacity: 0.7;
}

.send-btn {
  padding: 10px 18px;
  border: 1px solid rgb(190, 232, 255);
  border-radius: 6px;
  background: rgba(190, 232, 255, 0.2);
  color: rgb(190, 232, 255);
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  transition: all 0.2s;
  height: 42px;
}

.send-btn:hover:not(:disabled) {
  background: rgba(190, 232, 255, 0.3);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .ai-chat-section {
    padding: 16px;
  }

  .ai-bubble {
    max-width: 92%;
  }

  .ai-chat-input-row {
    flex-direction: column;
    align-items: stretch;
  }

  .send-btn {
    width: 100%;
  }
}
</style>
