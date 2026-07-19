const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(detail || `请求失败 (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

/** 把后端返回的 /uploads/... 转成可访问的完整地址 */
export function assetUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path) || path.startsWith("blob:")) return path;
  if (path.startsWith("/")) return `${API_BASE}${path}`;
  return `${API_BASE}/${path}`;
}

export const api = {
  getFootprints: () => request("/api/footprints"),
  getMessages: () => request("/api/messages"),
  createMessage: (nickname, content) =>
    request("/api/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nickname, content }),
    }),
  getDiary: (year, month) => request(`/api/diary?year=${year}&month=${month}`),
  saveDiary: (payload) =>
    request("/api/diary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  uploadDiaryImage: async (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/diary/image", { method: "POST", body: form });
  },
  deleteDiaryImage: (url, year, month, day) => {
    const params = new URLSearchParams({
      url,
      year: String(year),
      month: String(month),
      day: String(day),
    });
    return request(`/api/diary/image?${params}`, { method: "DELETE" });
  },
  getGallery: () => request("/api/gallery"),
  getChatHistory: () => request("/api/chat/history"),
  clearChatHistory: () => request("/api/chat/history", { method: "DELETE" }),
  /**
   * 流式聊天：通过 onDelta / onDone / onError 回调消费 SSE
   */
  chatStream: async (content, { onDelta, onDone, onError } = {}) => {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || JSON.stringify(body);
      } catch {
        // ignore
      }
      throw new Error(detail || `请求失败 (${res.status})`);
    }

    if (!res.body) {
      throw new Error("浏览器不支持流式响应");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const line = chunk.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.replace(/^data:\s*/, "");
        if (!payload) continue;

        let data;
        try {
          data = JSON.parse(payload);
        } catch {
          continue;
        }

        if (data.type === "delta" && data.content) {
          onDelta?.(data.content);
        } else if (data.type === "done") {
          onDone?.(data);
        } else if (data.type === "error") {
          const err = new Error(data.detail || "流式输出失败");
          onError?.(err);
          throw err;
        }
      }
    }
  },
};

export { API_BASE };
