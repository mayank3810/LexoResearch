import type { AsOf, CalendarItem, Claim, WorldModel, WorldSnapshot } from './types'

const base = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${base}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

function tape(world: WorldSnapshot) {
  return {
    bindings: world.bindings,
    starting_book: world.starting_book,
  }
}

export const api = {
  asOf: () => get<AsOf>('/as-of'),
  worldModel: (world?: string) =>
    get<WorldModel>(world ? `/world-model?world=${world}` : '/world-model'),
  calendar: () => get<{ items: CalendarItem[] }>('/calendar'),
  claim: (id: string) => get<Claim>(`/claims/${id}`),
  thesis: (world: string) =>
    get<{ thesis: WorldSnapshot['thesis']; tape_hash: string; awaiting_human: WorldSnapshot['awaiting_human']; factor_tilts: Record<string, string>; lit_node_ids: string[] }>(
      `/thesis-state?world=${world}`,
    ),
  world: (id: string) => get<WorldSnapshot>(`/worlds/${id}`),
  bind: (world: WorldSnapshot, event_id: string, outcome: string) =>
    post<WorldSnapshot>(`/worlds/${world.world_id}/bind`, {
      event_id,
      outcome,
      ...tape(world),
    }),
  adjudicate: (world: WorldSnapshot, event_id: string, outcome: string) =>
    post<WorldSnapshot>(`/worlds/${world.world_id}/adjudicate`, {
      event_id,
      outcome,
      ...tape(world),
    }),
  startingBook: (world: WorldSnapshot, starting_book: 'flat' | 'long') =>
    post<WorldSnapshot>(`/worlds/${world.world_id}/starting-book`, {
      starting_book,
      bindings: world.bindings,
    }),
  replay: (world: WorldSnapshot) =>
    post<WorldSnapshot & { hashes_match: boolean }>(`/worlds/${world.world_id}/replay`, tape(world)),
  reset: (id: string) => post<WorldSnapshot>(`/worlds/${id}/reset`),
}
