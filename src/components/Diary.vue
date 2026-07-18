<script setup>
import { ref, computed, onMounted } from "vue";
import { api, assetUrl } from "../api";

const currentDate = ref(new Date());
const selectedDay = ref(new Date().getDate());
const diaryList = ref([]);
const currentDiaryContent = ref("暂无日记");
const lastSaveTime = ref("");
const imageUrl = ref("");
const previewImage = ref("");
const fileInputRef = ref(null);
const isSaving = ref(false);
const isDeleting = ref(false);

const firstDayOfMonth = computed(() => {
  const year = currentDate.value.getFullYear();
  const month = currentDate.value.getMonth();
  return new Date(year, month, 1).getDay();
});

const daysInMonth = computed(() => {
  const year = currentDate.value.getFullYear();
  const month = currentDate.value.getMonth();
  return new Date(year, month + 1, 0).getDate();
});

const calendarGrid = computed(() => {
  const grid = [];
  const firstDay = firstDayOfMonth.value;
  const totalDays = daysInMonth.value;

  for (let i = 0; i < firstDay; i++) grid.push(null);
  for (let day = 1; day <= totalDays; day++) grid.push(day);

  const totalCells = Math.ceil(grid.length / 7) * 7;
  while (grid.length < totalCells) grid.push(null);

  const rows = [];
  for (let i = 0; i < grid.length; i += 7) {
    rows.push(grid.slice(i, i + 7));
  }
  return rows;
});

const weekTitles = ["Sun.", "Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat."];

const formatTime = (dateStr) => {
  if (!dateStr) return "无";
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${(d.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d
    .getHours()
    .toString()
    .padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
};

const resolveImage = (url) => assetUrl(url);

const updateCurrentDiary = () => {
  const found = diaryList.value.find(
    (item) =>
      item.day === selectedDay.value &&
      item.month === currentDate.value.getMonth() + 1 &&
      item.year === currentDate.value.getFullYear()
  );

  if (found) {
    currentDiaryContent.value = found.content || "暂无记录";
    lastSaveTime.value = formatTime(found.updated_at || found.created_at);
    imageUrl.value = found.image_url || "";
    previewImage.value = resolveImage(found.image_url || "");
  } else {
    currentDiaryContent.value = "暂无记录";
    lastSaveTime.value = "无";
    imageUrl.value = "";
    previewImage.value = "";
  }
};

const fetchDiary = async () => {
  try {
    const year = currentDate.value.getFullYear();
    const month = currentDate.value.getMonth() + 1;
    const data = await api.getDiary(year, month);
    diaryList.value = data || [];
    updateCurrentDiary();
  } catch (e) {
    console.error("读取日记失败:", e);
    alert("读取日记失败：" + e.message);
  }
};

const uploadImage = async (file) => {
  if (!file) return "";
  try {
    const data = await api.uploadDiaryImage(file);
    return data.url || "";
  } catch (e) {
    console.error("上传图片失败:", e);
    alert("上传图片失败：" + e.message);
    return "";
  }
};

const deleteImage = async () => {
  if (!previewImage.value && !imageUrl.value) return;
  if (!confirm("确定要删除这张图片吗？")) return;

  isDeleting.value = true;
  try {
    const year = currentDate.value.getFullYear();
    const month = currentDate.value.getMonth() + 1;
    const day = selectedDay.value;
    const url = imageUrl.value || previewImage.value;

    await api.deleteDiaryImage(url, year, month, day);

    previewImage.value = "";
    imageUrl.value = "";
    if (fileInputRef.value) fileInputRef.value.value = "";

    await fetchDiary();
    alert("图片删除成功！");
  } catch (e) {
    console.error("删除图片失败:", e);
    alert("删除图片失败：" + e.message);
  } finally {
    isDeleting.value = false;
  }
};

const handleFileChange = (e) => {
  const file = e.target.files?.[0];
  if (file) {
    previewImage.value = URL.createObjectURL(file);
  }
};

const saveDiary = async () => {
  if (
    !currentDiaryContent.value.trim() ||
    currentDiaryContent.value === "暂无记录"
  )
    return;

  isSaving.value = true;
  try {
    const year = currentDate.value.getFullYear();
    const month = currentDate.value.getMonth() + 1;
    const day = selectedDay.value;

    let finalImageUrl = imageUrl.value || "";
    const file = fileInputRef.value?.files?.[0];
    if (file) {
      const url = await uploadImage(file);
      if (url) {
        finalImageUrl = url;
        imageUrl.value = url;
        previewImage.value = resolveImage(url);
      }
    }

    await api.saveDiary({
      year,
      month,
      day,
      content: currentDiaryContent.value,
      image_url: finalImageUrl,
    });

    await fetchDiary();
    alert("保存成功！");
    if (fileInputRef.value) fileInputRef.value.value = "";
  } catch (e) {
    console.error("保存失败:", e);
    alert("保存失败：" + e.message);
  } finally {
    isSaving.value = false;
  }
};

const selectDay = (day) => {
  if (day) {
    selectedDay.value = day;
    updateCurrentDiary();
  }
};

onMounted(() => {
  fetchDiary();
});
</script>

<template>
  <div class="diary-section">
    <div class="diary-left">
      <div class="month-title">
        {{ currentDate.getFullYear() }}年{{ currentDate.getMonth() + 1 }}月
      </div>
      <div class="week-header">
        <div v-for="title in weekTitles" :key="title" class="week-cell">
          {{ title }}
        </div>
      </div>
      <div class="calendar-grid">
        <div
          v-for="(row, rowIndex) in calendarGrid"
          :key="rowIndex"
          class="calendar-row"
        >
          <div
            v-for="(day, colIndex) in row"
            :key="colIndex"
            class="calendar-cell"
            :class="{
              'has-day': !!day,
              active: day === selectedDay,
              today:
                day === new Date().getDate() &&
                currentDate.getMonth() === new Date().getMonth(),
            }"
            @click="selectDay(day)"
          >
            <!-- 点击查找当天日记 -->
            {{ day || "" }}
          </div>
        </div>
      </div>
    </div>

    <div class="diary-right">
      <div class="diary-header">
        <div>
          {{ currentDate.getFullYear() }}年{{ currentDate.getMonth() + 1 }}月{{
            selectedDay
          }}日
          <div class="save-time">最后更新于：{{ lastSaveTime }}</div>
        </div>
        <div class="header-buttons">
          <label class="upload-btn">
            上传图片
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              @change="handleFileChange"
              hidden
            />
          </label>
          <!-- 新增：删除图片按钮（有图片时显示） -->
          <button
            class="delete-btn"
            @click="deleteImage"
            :disabled="isDeleting || !previewImage"
            v-if="previewImage"
          >
            {{ isDeleting ? "删除中..." : "删除图片" }}
          </button>
          <button class="save-btn" @click="saveDiary" :disabled="isSaving">
            {{ isSaving ? "保存中..." : "保存" }}
          </button>
        </div>
      </div>

      <div class="diary-content-wrapper">
        <textarea
          v-model="currentDiaryContent"
          placeholder="在这里记录你的心情..."
          :disabled="isSaving || isDeleting"
        ></textarea>
        <div v-if="previewImage" class="image-preview">
          <img :src="previewImage" alt="图片预览" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diary-section {
  width: 100%;
  max-width: 1400px;
  margin: 20px auto 0;
  /* background: rgba(0, 0, 0, 0.4); */
  border-radius: 16px;
  padding: 25px;
  box-sizing: border-box;
  display: flex;
  gap: 25px;
  color: #fff;
  font-family: "Microsoft YaHei", sans-serif;
}

.diary-left {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.month-title {
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.week-header {
  display: flex;
  border-radius: 4px 4px 0 0;
}

.week-cell {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: #ccc;
}

.calendar-grid {
  border-radius: 0 0 8px 8px;
  padding: 10px;
}

.calendar-row {
  display: flex;
}

.calendar-cell {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  margin: 2px;
  transition: all 0.2s ease;
}

.calendar-cell:not(.has-day) {
  cursor: default;
  opacity: 0.2;
}

.calendar-cell.has-day:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.calendar-cell.active {
  background: rgba(190, 232, 255, 0.3);
  color: rgb(190, 232, 255);
  font-weight: bold;
}

.calendar-cell.today {
  border: 1px solid rgb(190, 232, 255);
}

.diary-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.diary-header {
  font-size: 22px;
  opacity: 0.9;
  border-left: 3px solid rgb(190, 232, 255);
  padding-left: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 10px;
}

.save-time {
  font-size: 15px;
  color: #999;
  margin-top: 5px;
  font-weight: normal;
}

.header-buttons {
  display: flex;
  gap: 8px;
}

.upload-btn,
.save-btn,
.delete-btn {
  /* 新增：删除按钮样式 */
  padding: 6px 12px;
  border: 1px solid rgb(190, 232, 255);
  border-radius: 6px;
  color: rgb(190, 232, 255);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  white-space: nowrap;
}

.upload-btn {
  background: rgba(190, 232, 255, 0.2);
}

.save-btn {
  background: rgba(190, 232, 255, 0.2);
}

/* 新增：删除按钮样式（红色系，区分保存按钮） */
.delete-btn {
  background: rgba(255, 107, 107, 0.2);
  border-color: rgb(255, 107, 107);
  color: rgb(255, 107, 107);
}

.upload-btn:hover {
  background: rgba(190, 232, 255, 0.3);
}

.save-btn:hover {
  background: rgba(190, 232, 255, 0.3);
}

/* 新增：删除按钮hover效果 */
.delete-btn:hover {
  background: rgba(255, 107, 107, 0.3);
}

.save-btn:disabled,
.delete-btn:disabled {
  /* 新增：删除按钮禁用样式 */
  opacity: 0.6;
  cursor: not-allowed;
}

.diary-content-wrapper {
  flex: 1;
  min-height: 350px;
  background: rgba(24, 24, 24, 0.2);
  backdrop-filter: blur(2px);
  border: none;
  border-radius: 12px;
  padding: 15px;
  color: #eee;
  font-size: 16px;
  line-height: 1.8;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.diary-content-wrapper textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #eee;
  font-size: 16px;
  line-height: 1.8;
  resize: none;
  outline: none;
}

.diary-content-wrapper textarea::placeholder {
  color: #999;
}

.image-preview {
  width: 100%;
  max-height: 200px;
  overflow: hidden;
  border-radius: 8px;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>