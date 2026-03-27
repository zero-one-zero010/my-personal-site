<script setup>
import { MapPin, Sunrise, Sunset } from "lucide-vue-next";
defineProps(["city"]);
</script>
<template>
  <div
    :style="{
      background: city.color,
      padding: '12px',
      borderRadius: '12px',
      color: 'white',
    }"
  >
    <div
      style="
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        opacity: 0.9;
        font-size: 25px;
      "
    >
      <span><MapPin :size="20" /> {{ city.name }}</span>
    </div>
    <div
      style="font-size: 30px; font-weight: bold; margin: 4px 0; font-size: 25px"
    >
      {{ city.temp }}
    </div>
    <div
      style="
        display: flex;
        gap: 8px;
        font-size: 10px;
        opacity: 0.8;
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        padding-top: 6px;
      "
    >
      <span
        style="display: flex; align-items: center; gap: 2px; font-size: 18px"
        ><Sunrise :size="25" /> {{ city.sunrise }}</span
      >
      <span
        style="display: flex; align-items: center; gap: 2px; font-size: 18px"
        ><Sunset :size="25" /> {{ city.sunset }}</span
      >
    </div>
  </div>
</template>