/**
 * Composable useWebSocket — gère la connexion WebSocket et alimente le store.
 *
 * Un composable Vue 3 est une fonction qui encapsule de la logique
 * réutilisable avec état. C'est l'équivalent des hooks React.
 * Convention : nom préfixé par "use".
 *
 * Ce composable est utilisé UNE SEULE FOIS dans App.vue.
 * Il expose les méthodes pour envoyer des messages (macro, capture, keybind).
 */

import { ref } from 'vue'
import { useGameStore } from '@/stores/game'
import type { GameState, Macro } from '@/types'

// Résultat retourné par le composable
export interface WsState {
  send: (msg: object) => void
  ackHint: ReturnType<typeof ref<string>>
}

export function useWebSocket(): WsState {
  const game = useGameStore()
  const ackHint = ref('')
  let ws: WebSocket | null = null

  function connect(): void {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}/ws`)

    ws.onopen = () => {
      game.applyPatch({ connected: true })
    }

    ws.onmessage = (ev: MessageEvent) => {
      const msg = JSON.parse(ev.data as string) as Record<string, unknown>

      switch (msg.type) {
        case 'snapshot':
          game.applySnapshot(msg.state as GameState)
          break

        case 'patch':
          game.applyPatch(msg.changes as Record<string, unknown>)
          break

        case 'macros':
          game.setMacros(msg.macros as Macro[])
          break

        case 'macro_ack': {
          const ack = msg as { id: string; ok: boolean }
          ackHint.value = ack.ok ? `✓ ${ack.id}` : `✗ ${ack.id}`
          setTimeout(() => (ackHint.value = ''), 1200)
          break
        }

        case 'keybind_updated': {
          const upd = msg as { id: string; ok: boolean; keyspec: Macro['key'] }
          if (upd.ok) {
            game.updateMacroKey(upd.id, upd.keyspec)
            ackHint.value = `✓ ${upd.id} → ${upd.keyspec.label}`
            setTimeout(() => (ackHint.value = ''), 1800)
          }
          break
        }
      }
    }

    ws.onclose = () => {
      game.applyPatch({ connected: false })
      setTimeout(connect, 1500)
    }

    ws.onerror = () => ws?.close()
  }

  function send(msg: object): void {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg))
    }
  }

  connect()

  return { send, ackHint }
}
