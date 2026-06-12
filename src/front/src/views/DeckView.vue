<template>
  <div>
    <section class="panel" style="margin-bottom:14px">
      <h2>
        Commandes
        <span class="ack-hint">{{ ackHint }}</span>
        <button
          class="cfg-toggle"
          :class="{ on: configuring }"
          @click="configuring = !configuring"
        >
          ⚙ Configurer
        </button>
      </h2>

      <div class="macro-grid">
        <MacroButton
          v-for="macro in game.macros"
          :key="macro.id"
          :macro="macro"
          :is-active="isMacroActive(macro)"
          @click="onMacroClick"
        />
      </div>
    </section>

    <!-- Modal de configuration (monté seulement si ouvert) -->
    <KeybindModal
      v-if="editingMacro"
      :macro="editingMacro"
      :send="send"
      ref="modalRef"
      @close="editingMacro = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useGameStore } from '@/stores/game'
import MacroButton from '@/components/MacroButton.vue'
import KeybindModal from '@/components/KeybindModal.vue'
import type { Macro, KeySpec } from '@/types'

const props = defineProps<{
  send: (msg: object) => void
  ackHint: string
}>()

const game        = useGameStore()
const configuring = ref(false)
const editingMacro = ref<Macro | null>(null)
const modalRef    = ref<InstanceType<typeof KeybindModal> | null>(null)

function isMacroActive(macro: Macro): boolean {
  return macro.status_flag
    ? !!(game.status as Record<string, unknown>)[macro.status_flag]
    : false
}

function onMacroClick(macro: Macro): void {
  if (configuring.value) {
    editingMacro.value = macro
    return
  }
  props.send({ type: 'macro', id: macro.id })
}

// Appelé depuis App.vue quand capture_result arrive via WS
function onCaptureResult(keyspec: KeySpec | null, error?: string): void {
  modalRef.value?.onCaptureResult(keyspec, error)
}

defineExpose({ onCaptureResult })
</script>
