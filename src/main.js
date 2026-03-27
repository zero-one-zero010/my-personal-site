import './style.css'
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'

// ========== 背景自动切换核心代码 ==========
// 1. 定义早晚背景图（替换成你的图片链接/本地路径）
const bgConfig = {
    morning: {
        url: "/842f0d17a4a59407ca2c14f7cbb5978c3816626.jpg", // 早上背景（晨光/晨景）
        // mask: "rgba(0, 0, 0, 0.5)" // 浅遮罩（更明亮）
    },
    evening: {
        url: "https://picsum.photos/id/1048/1920/1080", // 晚上背景（夜景/暖光）
        mask: "rgba(0, 0, 0, 0.8)" // 深遮罩（适配夜景）
    }
};

// 2. 判断当前时间段（早/晚，19点切换）
function getCurrentBgType() {
    const hour = new Date().getHours();
    return hour >= 19 ? "evening" : "morning";
}

// 3. 设置背景样式
function setBackground() {
    const bgType = getCurrentBgType();
    const body = document.body;

    // 核心样式：铺满屏幕 + 固定 + 遮罩
    body.style.background = `url(${bgConfig[bgType].url}) no-repeat center center fixed`;
    body.style.backgroundSize = "cover";
    body.style.backgroundColor = bgConfig[bgType].mask;
    body.style.backgroundBlendMode = "overlay";
    body.style.minHeight = "100vh";
    body.style.margin = "0";
    body.style.padding = "0";
    body.style.transition = "background 1s ease"; // 切换动画（丝滑）
}

// 4. 初始化 + 每分钟检查时间（确保19点准时切换）
setBackground(); // 页面加载时立即生效
setInterval(setBackground, 60 * 1000); // 每分钟检查一次时间
// ========== 背景切换代码结束 ==========


createApp(App).use(router).mount('#app')

// // main.js
// import { createApp } from 'vue'
// import App from './App.vue'

// // ========== 背景自动切换核心代码 ==========
// // 1. 定义早晚背景图（替换成你的图片链接/本地路径）
// const bgConfig = {
//     morning: {
//         url: "/842f0d17a4a59407ca2c14f7cbb5978c3816626.jpg", // 早上背景（晨光/晨景）
//         mask: "rgba(0, 0, 0, 0.5)" // 浅遮罩（更明亮）
//     },
//     evening: {
//         url: "https://picsum.photos/id/1048/1920/1080", // 晚上背景（夜景/暖光）
//         mask: "rgba(0, 0, 0, 0.8)" // 深遮罩（适配夜景）
//     }
// };

// // 2. 判断当前时间段（早/晚，19点切换）
// function getCurrentBgType() {
//     const hour = new Date().getHours();
//     return hour >= 19 ? "evening" : "morning";
// }

// // 3. 设置背景样式
// function setBackground() {
//     const bgType = getCurrentBgType();
//     const body = document.body;

//     // 核心样式：铺满屏幕 + 固定 + 遮罩
//     body.style.background = `url(${bgConfig[bgType].url}) no-repeat center center fixed`;
//     body.style.backgroundSize = "cover";
//     body.style.backgroundColor = bgConfig[bgType].mask;
//     body.style.backgroundBlendMode = "overlay";
//     body.style.minHeight = "100vh";
//     body.style.margin = "0";
//     body.style.padding = "0";
//     body.style.transition = "background 1s ease"; // 切换动画（丝滑）
// }

// // 4. 初始化 + 每分钟检查时间（确保19点准时切换）
// setBackground(); // 页面加载时立即生效
// setInterval(setBackground, 60 * 1000); // 每分钟检查一次时间
// // ========== 背景切换代码结束 ==========

// // 创建Vue应用（你的原有代码）
// createApp(App).mount('#app')