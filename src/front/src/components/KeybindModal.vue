<template>
  <Teleport to="body">
    <div class="modal-bg" @click.self="emit('close')">
      <div class="modal">
        <h3>Configurer · {{ macro?.label }}</h3>
        <div class="sub">Touche envoyée à Elite Dangerous pour cette commande.</div>

        <div class="current">
          <span class="lbl">Raccourci actuel</span>
          <span class="val">{{ preview || '—' }}</span>
        </div>

        <div class="section">
          <div class="title">1 · Détecter une touche</div>
          <button
            class="mbtn"
            :class="{ detecting }"
            :disabled="detecting"
            @click="startCapture"
          >
            {{ detecting ? 'Appuyez sur une touche du PC…' : 'Appuyer sur une touche…' }}
          </button>
        </div>

        <div class="section">
          <div class="title">2 · Ou saisir un code / nom</div>
          <div class="code-row">
            <input v-model="codeInput" placeholder="ex : f13, home, g, vk:135">
            <button class="mbtn" style="width:auto" @click="applyCode">OK</button>
          </div>
          <div class="mods">
            <label><input type="checkbox" v-model="modCtrl"> Ctrl</label>
            <label><input type="checkbox" v-model="modShift"> Shift</label>
            <label><input type="checkbox" v-model="modAlt"> Alt</label>
          </div>
          <div class="quick">
            <button v-for="k in QUICK_KEYS" :key="k" @click="codeInput = k">
              {{ k.toUpperCase().replace('_', ' ') }}
            </button>
          </div>
        </div>

        <div class="actions">
          <button class="mbtn primary" @click="save">Enregistrer</button>
          <button class="mbtn" @click="emit('close')">Annuler</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Macro, KeySpec } from '@/types'

const props = defineProps<{
  macro: Macro | null
  send: (msg: object) => void
}>()

const emit = defineEmits<{
  close: []
  captured: [keyspec: KeySpec]
}>()

const QUICK_KEYS = ['f13', 'f14', 'f15', 'f16', 'home', 'insert', 'delete', 'numpad_0']

const preview   = ref('')
const codeInput = ref('')
const modCtrl   = ref(false)
const modShift  = ref(false)
const modAlt    = ref(false)
const detecting = ref(false)
const pending   = ref<Partial<KeySpec>>({})

// Initialise quand la macro change
watch(() => props.macro, (m) => {
  if (!m) return
  preview.value   = m.key?.label || '—'
  codeInput.value = ''
  modCtrl.value   = m.key?.modifiers.includes('ctrl') ?? false
  modShift.value  = m.key?.modifiers.includes('shift') ?? false
  modAlt.value    = m.key?.modifiers.includes('alt') ?? false
  pending.value   = m.key ? { ...m.key } : {}
  detecting.value = false
})

function currentModifiers(): string[] {
  const m: string[] = []
  if (modCtrl.value)  m.push('ctrl')
  if (modShift.value) m.push('shift')
  if (modAlt.value)   m.push('alt')
  return m
}

function startCapture(): void {
  detecting.value = true
  props.send({ type: 'capture_start' })
}

// Appelé par le parent quand capture_result arrive
function onCaptureResult(keyspec: KeySpec | null, error?: string): void {
  detecting.value = false
  if (keyspec) {
    pending.value   = { ...keyspec }
    modCtrl.value   = keyspec.modifiers.includes('ctrl')
    modShift.value  = keyspec.modifiers.includes('shift')
    modAlt.value    = keyspec.modifiers.includes('alt')
    preview.value   = keyspec.label
  } else {
    preview.value = error ?? 'aucune touche'
  }
}

function applyCode(): void {
  const raw = codeInput.value.trim().toLowerCase()
  if (!raw) return
  const spec: Partial<KeySpec> = { modifiers: currentModifiers() }
  if (raw.startsWith('vk:')) {
    const vk = parseInt(raw.slice(3), 10)
    if (!isNaN(vk)) spec.vk = vk
  } else if (/^[a-z]$/.test(raw)) {
    spec.char = raw
  } else {
    spec.name = raw
  }
  const mod = spec.modifiers?.length
    ? spec.modifiers.map(m => m[0].toUpperCase() + m.slice(1)).join('+') + '+'
    : ''
  const base = spec.name
    ? spec.name.toUpperCase().replace('_', ' ')
    : spec.char ? spec.char.toUpperCase()
    : spec.vk != null ? `VK ${spec.vk}` : '—'
  spec.label = mod + base
  pending.value = spec
  preview.value = spec.label
}

function save(): void {
  if (!props.macro || !pending.value) { emit('close'); return }
  pending.value.modifiers = currentModifiers()
  props.send({
    type: 'set_keybind',
    id: props.macro.id,
    keyspec: pending.value,
  })
  emit('close')
}

defineExpose({ onCaptureResult })
</script>
