<!-- ProfileSection.vue -->
<script setup>
import { ref, onMounted } from "vue";
import { createClient } from "@supabase/supabase-js";

// 1. 初始化Supabase（替换成你的实际KEY，桶名已改）
const SUPABASE_URL = "https://qqrueinnfqmccfwiqczw.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_3PP6lvPA8MWhZFpdac3O4w_eWtwDlF0";
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 个人信息数据（完全保留你的配置）
const profileData = ref({
  avatar: "/头像.jpg", // 头像用Public文件夹
  nickname: "Zero",
  birthday: "2005-07",
  constellation: "狮子座🦁",
  mbti: "ISFJ",
  siteStartDate: "2026年03月",
  hobbies: ["羽毛球", "摄影", "旅行", "阅读"],
  city: "广东 广州",
  school: "华南农业大学",
  subject: "计算机科学与技术",
  age: "21",
  qianming: "慢热喜静，往自由里去🌿",
});

// 影像集核心配置
const photoGallery = ref([]); // 存储Supabase读取的图片URL
const isLoading = ref(true); // 加载状态
const activeIndex = ref(0); // 当前选中的大图索引
const placeholderImg = "https://via.placeholder.com/800x500?text=暂无图片"; // 大图占位

// 2. 从Supabase读取影像集图片（适配桶名profile-gallery + 无子文件夹）
const getSupabaseGallery = async () => {
  try {
    isLoading.value = true;
    // 关键修改：桶名改为profile-gallery，读取根目录（空字符串表示根目录）
    const { data: galleryFiles, error } = await supabase.storage
      .from("my-site-files") // 你的实际桶名
      .list("profile-gallery", {
        // 空字符串 = 读取桶的根目录（无子文件夹）
        limit: 100,
        offset: 0,
        sortBy: { column: "name", order: "asc" },
      });

    if (error) throw error;

    // 转换为公开访问URL（同样适配根目录）
    const galleryUrls = [];
    for (const file of galleryFiles) {
      // 过滤系统文件（如.DS_Store）
      if (!file.name.includes(".DS_Store")) {
        const { data: urlData } = supabase.storage
          .from("my-site-files") // 你的实际桶名
          .getPublicUrl(`profile-gallery/${file.name}`); // 根目录直接用文件名，无需文件夹前缀
        galleryUrls.push(urlData.publicUrl);
      }
    }

    photoGallery.value = galleryUrls;
    activeIndex.value = galleryUrls.length > 0 ? 0 : -1; // 有图片默认选第一张
  } catch (e) {
    console.error("读取影像集失败:", e);
    photoGallery.value = [];
  } finally {
    isLoading.value = false;
  }
};

// 3. 切换大图方法（新增上一张/下一张逻辑）
const switchImage = (index) => {
  activeIndex.value = index;
};

// 新增：上一张
const prevImage = () => {
  if (photoGallery.value.length === 0) return;
  activeIndex.value =
    (activeIndex.value - 1 + photoGallery.value.length) %
    photoGallery.value.length;
};

// 新增：下一张
const nextImage = () => {
  if (photoGallery.value.length === 0) return;
  activeIndex.value = (activeIndex.value + 1) % photoGallery.value.length;
};

// 4. 页面加载时初始化
onMounted(() => {
  getSupabaseGallery();
});
</script>

<template>
  <div class="profile-section">
    <!-- 左侧：个人信息（完全保留你的结构） -->
    <div class="profile-info">
      <div class="profile-header">
        <img :src="profileData.avatar" alt="头像" class="avatar" />
        <h2 class="nickname">{{ profileData.nickname }}</h2>
      </div>
      <div class="profile-details">
        <div class="detail-item">
          <span class="label">出生年月：</span>
          <span class="value">{{ profileData.birthday }}</span>
        </div>
        <div class="detail-item">
          <span class="label">年龄：</span>
          <span class="value">{{ profileData.age }}</span>
        </div>
        <div class="detail-item">
          <span class="label">星座：</span>
          <span class="value">{{ profileData.constellation }}</span>
        </div>
        <div class="detail-item">
          <span class="label">MBTI：</span>
          <span class="value">{{ profileData.mbti }}</span>
        </div>
        <div class="detail-item">
          <span class="label">爱好：</span>
          <span class="value">{{ profileData.hobbies.join("、") }}</span>
        </div>
        <div class="detail-item">
          <span class="label">网站创建：</span>
          <span class="value">{{ profileData.siteStartDate }}</span>
        </div>
        <div class="detail-item">
          <span class="label">城市：</span>
          <span class="value">{{ profileData.city }}</span>
        </div>
        <div class="detail-item">
          <span class="label">学校：</span>
          <span class="value">{{ profileData.school }}</span>
        </div>
        <div class="detail-item">
          <span class="label">专业：</span>
          <span class="value">{{ profileData.subject }}</span>
        </div>
        <div class="detail-item">
          <span class="label">个性签名：</span>
          <span class="value">{{ profileData.qianming }}</span>
        </div>
      </div>
    </div>

    <!-- 右侧：个人影像集（大图+小图导航 + 悬浮显示切换按钮） -->
    <div class="photo-gallery">
      <h3 class="gallery-title">个人影像集</h3>

      <!-- 加载状态提示 -->
      <div v-if="isLoading" class="gallery-loading">影像集加载中...</div>

      <!-- 无图片提示 -->
      <div v-else-if="!photoGallery.length" class="gallery-empty">
        暂无影像集图片
      </div>

      <!-- 影像集主体（大图+小图导航） -->
      <div v-else class="gallery-container">
        <!-- 顶部大图预览（悬浮显示切换按钮） -->
        <div class="gallery-main-img">
          <!-- 新增：上一张按钮（默认隐藏） -->
          <button class="img-nav-btn prev-btn" @click="prevImage">&lt;</button>
          <img
            :src="photoGallery[activeIndex] || placeholderImg"
            alt="当前预览图片"
            class="main-img"
          />
          <!-- 新增：下一张按钮（默认隐藏） -->
          <button class="img-nav-btn next-btn" @click="nextImage">&gt;</button>
        </div>

        <!-- 底部小图导航（横向滚动） -->
        <div class="gallery-thumbnails">
          <div
            class="thumbnail-item"
            v-for="(img, index) in photoGallery"
            :key="index"
            @click="switchImage(index)"
            :class="{ active: index === activeIndex }"
          >
            <img :src="img" alt="缩略图" class="thumbnail-img" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-section {
  display: flex;
  gap: 20px;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 20px;
  color: #fff;
}

.profile-info {
  width: 36%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgb(190, 232, 255);
}

.nickname {
  font-size: 22px;
  font-weight: bold;
  color: rgb(190, 232, 255);
  margin: 0;
  margin-bottom: 20px;
}

.profile-details {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 15px;
}

.detail-item {
  display: flex;
  justify-content: flex-start;
  gap: 8px;
  margin-bottom: 10px;
  margin-left: 20px;
}

.detail-item .value {
  margin-left: 15px;
}

.label {
  color: #ccc;
  min-width: 80px;
}

.value {
  color: #fff;
}

/* 右侧影像集 */
.photo-gallery {
  width: 64%;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.gallery-title {
  font-size: 20px;
  color: rgb(190, 232, 255);
  margin: 0;
}

.gallery-loading,
.gallery-empty {
  text-align: center;
  padding: 20px;
  color: #ccc;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.gallery-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

/* 大图高度改矮：核心修改 */
.gallery-main-img {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 260px; /* 变矮了 */
  position: relative;
}

.img-nav-btn {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
  border: none;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
  opacity: 0;
  pointer-events: none;
}

.gallery-main-img:hover .img-nav-btn {
  opacity: 1;
  pointer-events: auto;
}

.prev-btn {
  left: 20px;
}

.next-btn {
  right: 20px;
}

.img-nav-btn:hover {
  background: rgba(255, 255, 255, 0.8);
  color: #000;
  transform: scale(1.05);
}

.main-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: all 0.3s ease;
}

.gallery-thumbnails {
  display: flex;
  gap: 10px;
  padding: 5px;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: rgb(190, 232, 255) transparent;
}

.gallery-thumbnails::-webkit-scrollbar {
  height: 6px;
}
.gallery-thumbnails::-webkit-scrollbar-thumb {
  background-color: rgb(190, 232, 255);
  border-radius: 3px;
}
.gallery-thumbnails::-webkit-scrollbar-track {
  background: transparent;
}

.thumbnail-item {
  width: 70px;
  height: 50px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  opacity: 0.7;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.thumbnail-item.active {
  opacity: 1;
  border-color: rgb(190, 232, 255);
}

.thumbnail-item:hover {
  opacity: 0.9;
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ====================== 正常响应式 ====================== */
@media (max-width: 1024px) {
  .profile-section {
    flex-direction: column;
  }
  .profile-info,
  .photo-gallery {
    width: 100%;
  }
  .gallery-main-img {
    min-height: 220px;
  }
  .img-nav-btn {
    width: 35px;
    height: 35px;
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .gallery-main-img {
    min-height: 180px;
  }
  .thumbnail-item {
    width: 60px;
    height: 45px;
  }
  .img-nav-btn {
    width: 30px;
    height: 30px;
    font-size: 14px;
    left: 10px;
    right: 10px;
  }
  .avatar {
    width: 100px;
    height: 100px;
  }
}
</style>