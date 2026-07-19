# My Footprints · 我的足迹

个人主页 / 足迹站点：用一张地图串联去过的城市，并集成天气卡片、音乐播放、日记、留言弹幕与 AI 对话等模块。

前端为 **Vue 3 + Vite**，后端为 **FastAPI + SQLite**，AI 对话对接 **DeepSeek**（OpenAI 兼容接口）。

---

## 功能概览

| 模块 | 说明 |
|------|------|
| 足迹地图 | 高德地图展示北京 / 广州 / 杭州 / 深圳等城市标记，点击天气卡片可飞向对应城市 |
| 天气卡片 | 展示城市温度、日出日落（数据来自后端 `footprints` 表） |
| 个人名片 | 头像、简介、爱好、影像集轮播 |
| 音乐播放 | 本地 BGM + 歌词滚动 |
| 时钟 / 问候 | 实时时钟，以及按时段切换的问候横幅；背景图按昼夜自动切换 |
| 留言弹幕 | 访客留言，滚动弹幕展示 |
| 日记 | 按日历写日记，支持配图上传与删除 |
| AI 聊天 | 流式对话（SSE），历史记录持久化，可清空 |

---

## 技术栈

**前端**

- Vue 3（`<script setup>`）+ Vue Router
- Vite 7
- Tailwind CSS 4
- lucide-vue-next（图标）
- 高德地图 JS API 2.0

**后端**

- FastAPI + Uvicorn
- SQLite（`backend/data.db`）
- OpenAI Python SDK（指向 DeepSeek API）

---

## 目录结构

```
my-footprints/
├── src/
│   ├── components/     # 天气、日记、AI 聊天、弹幕、播放器等
│   ├── views/          # 页面（HomeView）
│   ├── api.js          # 前端 API 封装
│   ├── router.js
│   └── main.js
├── backend/
│   ├── main.py         # FastAPI 入口与接口
│   ├── init_db.py      # 初始化数据库与示例足迹数据
│   ├── data.db         # SQLite 数据库（本地生成）
│   ├── uploads/        # 日记图、影像集等静态文件
│   ├── .env.example    # 后端环境变量示例
│   └── .env            # 本地密钥（勿提交）
├── public/             # 静态资源（背景图等）
├── index.html          # 含高德地图 Key 配置
└── package.json
```

---

## 环境要求

- Node.js 18+（建议 LTS）
- Python 3.10+
- 高德开放平台 Web 端 Key（地图）
- DeepSeek API Key（AI 聊天，可选；不配则聊天接口不可用）

---

## 快速开始

### 1. 克隆并安装前端依赖

```bash
npm install
```

### 2. 配置前端环境变量（可选）

在项目根目录创建 `.env`（可参考已有本地配置）：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

不配置时默认请求 `http://127.0.0.1:8000`。

### 3. 配置高德地图

编辑 `index.html`，将其中的 Key / 安全密钥换成你自己的：

```html
window._AMapSecurityConfig = { securityJsCode: "你的安全密钥" };
<!-- maps?v=2.0&key=你的Key&plugin=... -->
```

### 4. 启动后端

```bash
cd backend

# 建议使用虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install fastapi uvicorn openai

# 初始化数据库（首次必跑）
python init_db.py

# 配置 DeepSeek（AI 聊天需要）
# 复制 .env.example 为 .env，填入密钥
# DEEPSEEK_API_KEY=sk-xxxx
# DEEPSEEK_MODEL=deepseek-chat

uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

后端启动后可访问：

- 健康检查：http://127.0.0.1:8000/api/health
- 接口文档：http://127.0.0.1:8000/docs

### 5. 启动前端

在项目根目录另开一个终端：

```bash
npm run dev
```

浏览器打开控制台提示的地址（一般为 http://localhost:5173）。

---

## 环境变量说明

### 前端（项目根目录 `.env`）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 根地址 | `http://127.0.0.1:8000` |

### 后端（`backend/.env`）

| 变量 | 说明 | 示例 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-...` |
| `DEEPSEEK_MODEL` | 模型名 | `deepseek-chat` |

可参考 `backend/.env.example`。`.env` 已在 `.gitignore` 中，请勿提交密钥。

---

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/footprints` | 城市足迹 / 天气摘要 |
| GET / POST | `/api/messages` | 留言列表 / 发表留言 |
| GET / POST | `/api/diary` | 按年月查询 / 保存日记 |
| POST / DELETE | `/api/diary/image` | 日记配图上传 / 删除 |
| GET | `/api/gallery` | 影像集图片列表 |
| GET / DELETE | `/api/chat/history` | 聊天历史 / 清空 |
| POST | `/api/chat` | AI 流式对话（SSE） |

静态上传文件通过 `/uploads/...` 访问。

---

## 常用脚本

```bash
npm run dev       # 开发服务器
npm run build     # 生产构建
npm run preview   # 预览构建产物
```

---

## 开发说明

- 后端 CORS 已允许 `http://localhost:5173` 与 `http://127.0.0.1:5173`。
- Vite 中配置了和风天气代理路径 `/qweather-api`（如后续接入实时天气可用）。
- 日记图保存在 `backend/uploads/diary/`，影像集在 `backend/uploads/gallery/`。
- AI 回复为 SSE 流式输出，前端在 `src/api.js` 的 `chatStream` 中消费。

---

## 许可证

私人项目 / 学习用途。如需开源分发，请自行补充许可证并更换文中的第三方 API Key。
