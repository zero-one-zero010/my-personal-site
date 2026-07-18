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
};

export { API_BASE };
