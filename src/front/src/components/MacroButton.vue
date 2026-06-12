<template>
  <button
    class="macro"
    :class="[macro.accent, { on: isActive, flash: flashing }]"
    @click="emit('click', macro)"
  >
    <span class="cat">{{ macro.category }}</span>
    {{ macro.label }}
    <span class="bind">
      {{ macro.kind === 'sequence' ? 'séquence' : (macro.key?.label || '—') }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Macro } from '@/types'

const props = defineProps<{
  macro: Macro
  isActive: boolean
}>()

const emit = defineEmits<{
  click: [macro: Macro]
}>()

// Flash à l'appui — géré localement dans le composant
const flashing = ref(false)

defineExpose({
  flash() {
    flashing.value = false
    requestAnimationFrame(() => {
      flashing.value = true
      setTimeout(() => (flashing.value = false), 400)
    })
  },
})
</script>
