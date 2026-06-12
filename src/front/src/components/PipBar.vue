<template>
  <div class="pipgroup" :class="group">
    <div class="label">{{ label }}</div>
    <div class="pipbars">
      <div
        v-for="i in 4"
        :key="i"
        class="pipbar"
        :class="{ fill: pipFilled(i) }"
      ></div>
    </div>
    <div class="num">{{ display }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  group: 'sys' | 'eng' | 'wep'
  value: number   // demi-pips 0-8
}>()

// Chaque pip représente 2 demi-pips
function pipFilled(i: number): boolean {
  return Math.max(0, Math.min(2, props.value - (i - 1) * 2)) > 0
}

const display = computed(() => (props.value / 2).toFixed(1))
</script>
