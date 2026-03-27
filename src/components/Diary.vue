<script setup>
// 组件挂载 → 拉取当月日记 → 生成日历网格 → 点击日期加载日记
// → 编辑 / 上传图片 → 保存 / 删除（同步数据库 + 存储）
import { ref, computed, onMounted } from "vue";
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = "https://qqrueinnfqmccfwiqczw.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_3PP6lvPA8MWhZFpdac3O4w_eWtwDlF0";
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const currentDate = ref(new Date());
const selectedDay = ref(new Date().getDate());
const diaryList = ref([]);
const currentDiaryContent = ref("暂无日记");
const lastSaveTime = ref("");
const imageUrl = ref("");
const previewImage = ref("");
const fileInputRef = ref(null);
const isSaving = ref(false);
const isDeleting = ref(false); // 新增：删除加载状态
// 依赖变化自动重新计算
// 计算当月第一天是星期几（0=周日，6=周六）
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

// 生成日历网格（最终渲染到页面的二维数组）
const calendarGrid = computed(() => {
  const grid = [];
  const firstDay = firstDayOfMonth.value;
  const totalDays = daysInMonth.value;

  // 月初补空（比如3月1日是周六，前面补0-5共6个null）
  for (let i = 0; i < firstDay; i++) grid.push(null);

  // 添加每一天
  for (let day = 1; day <= totalDays; day++) grid.push(day);

  // 月末补空
  const totalCells = Math.ceil(grid.length / 7) * 7;
  while (grid.length < totalCells) grid.push(null);

  // 拆分成二维数组
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
    // （2，0）确保两位数03
    .getHours()
    .toString()
    .padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
};
// 从当月日记列表里，找“年/月/日”匹配的日记
const updateCurrentDiary = () => {
  const found = diaryList.value.find(
    (item) =>
      item.day === selectedDay.value &&
      item.month === currentDate.value.getMonth() + 1 &&
      item.year === currentDate.value.getFullYear()
  );

  if (found) {
    // 找到了就显示
    currentDiaryContent.value = found.content || "暂无记录";
    lastSaveTime.value = formatTime(found.updated_at || found.created_at);
    imageUrl.value = found.image_url || "";
    previewImage.value = found.image_url || "";
  } else {
    currentDiaryContent.value = "暂无记录";
    lastSaveTime.value = "无";
    imageUrl.value = "";
    previewImage.value = "";
  }
};

// 从数据库拉取当月所有日记
const fetchDiary = async () => {
  try {
    const year = currentDate.value.getFullYear();
    // 当年当月
    const month = currentDate.value.getMonth() + 1;

    const { data, error } = await supabase
      .from("diary")
      .select("*")
      .eq("year", year)
      .eq("month", month);

    if (error) throw error;
    // 把数据存到日记数组里
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
    const fileName = `${Date.now()}_${Math.random()
      .toString(36)
      .slice(2, 10)}_${file.name}`;
    // 上传图片到 Supabase Storage 的 diary-images 桶
    const { data, error } = await supabase.storage
      .from("diary-images")
      .upload(fileName, file, { upsert: true });

    if (error) throw error;
    // 获取图片的公共访问URL
    const { data: urlData } = supabase.storage
      .from("diary-images")
      .getPublicUrl(fileName);

    return urlData.publicUrl;
  } catch (e) {
    console.error("上传图片失败:", e);
    alert("上传图片失败：" + e.message);
    return "";
  }
};

// 新增：删除图片函数
// 删除-数据库删除-刷新（重新拉取）
const deleteImage = async () => {
  if (!previewImage.value) return; // 无图片时不执行
  if (!confirm("确定要删除这张图片吗？")) return; // 确认删除

  isDeleting.value = true;
  try {
    // 1. 从URL解析出文件名（关键：提取Storage中的文件名）
    const urlParts = previewImage.value.split("/");
    const fileName = urlParts[urlParts.length - 1];

    // 2. 删除Storage中的图片文件
    const { error: storageError } = await supabase.storage
      .from("diary-images")
      .remove([fileName]);

    if (storageError) throw storageError;

    // 3. 清空数据库中的image_url字段
    const year = currentDate.value.getFullYear();
    const month = currentDate.value.getMonth() + 1;
    const day = selectedDay.value;

    const { data: existing, error: fetchError } = await supabase
      .from("diary")
      .select("id")
      .eq("year", year)
      .eq("month", month)
      .eq("day", day)
      .single();

    if (fetchError && fetchError.code !== "PGRST116") throw fetchError;

    if (existing?.id) {
      await supabase
        .from("diary")
        .update({ image_url: "", updated_at: new Date().toISOString() })
        .eq("id", existing.id);
    }

    // 4. 清空页面预览
    previewImage.value = "";
    imageUrl.value = "";
    // 清空文件选择框
    if (fileInputRef.value) fileInputRef.value.value = "";

    // 5. 刷新数据，重新拉取
    await fetchDiary();
    alert("图片删除成功！");
  } catch (e) {
    console.error("删除图片失败:", e);
    alert("删除图片失败：" + e.message);
  } finally {
    isDeleting.value = false;
  }
};
// 选择图片后预览
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
    const now = new Date().toISOString();
    // 查该日期是否已有日记（有则更新，无则新增）
    const { data: existing, error } = await supabase
      .from("diary")
      .select("id, image_url")
      .eq("year", year)
      .eq("month", month)
      .eq("day", day)
      .single();

    let existingId = null;
    let finalImageUrl = existing?.image_url || "";
    if (!error) {
      existingId = existing.id;
    } else if (error.code !== "PGRST116") {
      throw error;
    }
    // 如果选了新图片，上传并更新URL
    const file = fileInputRef.value?.files?.[0];
    if (file) {
      const url = await uploadImage(file);
      if (url) {
        finalImageUrl = url;
        previewImage.value = url;
      }
    }
    // 有记录：更新内容和图片
    if (existingId) {
      await supabase
        .from("diary")
        .update({
          content: currentDiaryContent.value,
          image_url: finalImageUrl,
          updated_at: now,
        })
        .eq("id", existingId);
    } else {
      // 无记录：新增一条，insert插入
      await supabase.from("diary").insert([
        {
          year,
          month,
          day,
          content: currentDiaryContent.value,
          image_url: finalImageUrl,
          created_at: now,
          updated_at: now,
        },
      ]);
    }

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
    // 加载日记
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