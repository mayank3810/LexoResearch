import { useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { CalendarItem, WorldSnapshot } from '../lib/types'
import { SourceCite } from './SourceCite'

type Props = {
  calendar: CalendarItem[]
  worldA: WorldSnapshot
  worldB: WorldSnapshot
  onChange: (world: 'A' | 'B', next: WorldSnapshot) => void
  onOpenClaim: (id: string) => void
}

export function WorkbenchView({ calendar, worldA, worldB, onChange, onOpenClaim }: Props) {
  const [replayNote, setReplayNote] = useState<string>('')

  async function replay(id: 'A' | 'B') {
    const current = id === 'A' ? worldA : worldB
    const result = await api.replay(current)
    onChange(id, result)
    setReplayNote(`${id} ${result.tape_hash.slice(0, 12)} · hashes match`)
  }

  return (
    <div className="px-6 py-5">
      <div className="mb-4 flex items-center justify-between gap-4 border border-[#c9a227]/40 bg-[#c9a227]/10 px-4 py-2">
        <p className="mono text-[12px] tracking-[0.14em] text-[#c9a227]">
          SIMULATED — NOT MARKET DATA
        </p>
        <p className="text-[13px] text-[#cfc3aa]">
          Two tapes, one model. Bind outcomes to the same calendar. At least one world turns on a customer disclosure.
        </p>
      </div>
      {replayNote && <p className="mono mb-3 text-[11px] text-[#7cb87c]">{replayNote}</p>}
      <div className="grid gap-4 xl:grid-cols-2">
        <WorldColumn
          world={worldA}
          calendar={calendar}
          onChange={(next) => onChange('A', next)}
          onReplay={() => replay('A')}
          onOpenClaim={onOpenClaim}
        />
        <WorldColumn
          world={worldB}
          calendar={calendar}
          onChange={(next) => onChange('B', next)}
          onReplay={() => replay('B')}
          onOpenClaim={onOpenClaim}
        />
      </div>
      <footer className="mt-6 border border-[#3a3226] bg-[#1c1812] p-4 text-[13px] text-[#cfc3aa]">
        <p className="mono text-[11px] tracking-[0.14em] text-[#9a8b72] uppercase">Done looks like</p>
        <ul className="mt-2 grid gap-1 md:grid-cols-2">
          <li>Live thesis-state recaps the conclusion without a memo tab</li>
          <li>A lit edge opens the sentence that authorised it, or our policy</li>
          <li>World A and World B bind different outcomes to the same calendar</li>
          <li>World B turns on a customer’s capex disclosure, not a price</li>
          <li>SIMULATED — NOT MARKET DATA stays on this workbench</li>
          <li>Replay prints the same hash</li>
          <li>Human-observable nodes wait for a person</li>
        </ul>
      </footer>
    </div>
  )
}

function Spinner() {
  return (
    <span
      className="inline-block h-3 w-3 shrink-0 animate-spin rounded-full border border-current border-t-transparent"
      aria-hidden
    />
  )
}

function WorldColumn({
  world,
  calendar,
  onChange,
  onReplay,
  onOpenClaim,
}: {
  world: WorldSnapshot
  calendar: CalendarItem[]
  onChange: (next: WorldSnapshot) => void
  onReplay: () => Promise<void>
  onOpenClaim: (id: string) => void
}) {
  const [busy, setBusy] = useState<string | null>(null)
  const bound = useMemo(
    () => Object.fromEntries(world.bindings.map((b) => [b.event_id, b])),
    [world.bindings],
  )

  async function run(key: string, work: () => Promise<void>) {
    if (busy) return
    setBusy(key)
    try {
      await work()
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="border border-[#3a3226] bg-[#1c1812]">
      <header className="flex items-center justify-between border-b border-[#3a3226] px-4 py-3">
        <div>
          <p className="mono text-[11px] text-[#9a8b72]">SIMULATED WORLD {world.world_id}</p>
          <h2 className="text-[22px]">
            {world.thesis.scenario} · {world.thesis.rating} · {world.thesis.position}
          </h2>
        </div>
        <div className="flex flex-col items-end gap-2">
          <label className="mono text-[11px] text-[#9a8b72]">
            Starting book{' '}
            <select
              className="cursor-pointer bg-[#14110c] text-[#e8dcc4] disabled:cursor-wait"
              value={world.starting_book}
              disabled={busy !== null}
              onChange={(e) => {
                const value = e.target.value as 'flat' | 'long'
                void run('book', async () => {
                  onChange(await api.startingBook(world, value))
                })
              }}
            >
              <option value="flat">flat</option>
              <option value="long">already long</option>
            </select>
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy !== null}
              className="mono inline-flex cursor-pointer items-center gap-1.5 text-[11px] text-[#d4a017] disabled:cursor-wait disabled:opacity-60"
              onClick={() => void run('replay', onReplay)}
            >
              {busy === 'replay' && <Spinner />}
              Replay
            </button>
            <button
              type="button"
              disabled={busy !== null}
              className="mono inline-flex cursor-pointer items-center gap-1.5 text-[11px] text-[#9a8b72] disabled:cursor-wait disabled:opacity-60"
              onClick={() =>
                void run('reset', async () => {
                  onChange(await api.reset(world.world_id))
                })
              }
            >
              {busy === 'reset' && <Spinner />}
              Reset seed
            </button>
          </div>
        </div>
      </header>

      <p className="mono break-all px-4 pt-3 text-[10px] text-[#9a8b72]">hash {world.tape_hash}</p>

      <div className="grid gap-4 p-4 lg:grid-cols-2">
        <div>
          <h3 className="text-[16px]">Calendar · outcome cards</h3>
          <ul className="mt-2 space-y-3">
            {calendar.map((item) => {
              const current = bound[item.event_id]
              return (
                <li key={item.id} className="border border-[#3a3226] bg-[#241e16] p-3">
                  <p className="mono text-[10px] text-[#9a8b72]">
                    {item.date} · {item.event.entity}
                    {item.event.third_party ? ' · THIRD-PARTY' : ''}
                    {item.event.observability === 'human_observable' ? ' · HUMAN' : ''}
                  </p>
                  <p className="text-[14px]">{item.label}</p>
                  <p className="mt-1">
                    <SourceCite document={item.document} page={item.page} />
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {item.event.possible_outcomes.map((outcome) => {
                      const key = `${item.event_id}:${outcome}`
                      return (
                      <button
                        key={outcome}
                        type="button"
                        disabled={busy !== null}
                        onClick={() =>
                          void run(key, async () => {
                            const next =
                              item.event.observability === 'human_observable'
                                ? await api.adjudicate(world, item.event_id, outcome)
                                : await api.bind(world, item.event_id, outcome)
                            onChange(next)
                          })
                        }
                        className={`mono inline-flex cursor-pointer items-center gap-1.5 rounded-sm px-2 py-1 text-[10px] disabled:cursor-wait disabled:opacity-60 ${
                          current?.outcome === outcome
                            ? 'bg-[#d4a017] text-[#14110c]'
                            : 'bg-[#14110c] text-[#cfc3aa]'
                        }`}
                      >
                        {busy === key && <Spinner />}
                        {outcome.replaceAll('_', ' ')}
                      </button>
                      )
                    })}
                  </div>
                  {item.event.observability === 'human_observable' && !current?.adjudicated && (
                    <p className="mono mt-2 text-[10px] text-[#c9a227]">AWAITING HUMAN OBSERVATION</p>
                  )}
                </li>
              )
            })}
          </ul>
        </div>

        <div>
          <h3 className="text-[16px]">Ledger</h3>
          <ol className="mt-2 space-y-3">
            {world.ledger.length === 0 && <li className="text-[13px] text-[#9a8b72]">Empty tape.</li>}
            {world.ledger.map((step) => (
              <li key={step.seq} className="border border-[#3a3226] bg-[#241e16] p-3">
                <p className="mono text-[10px] text-[#9a8b72]">
                  {step.date} · {step.entity}
                  {step.third_party ? ' · THIRD-PARTY DISCLOSURE' : ''}
                </p>
                <p className="text-[14px]">
                  {step.event_name} → {step.outcome.replaceAll('_', ' ')}
                </p>
                {step.skipped ? (
                  <p className="mono mt-1 text-[10px] text-[#c9a227]">{step.skip_reason}</p>
                ) : (
                  <>
                    <p className="mt-1 text-[12px] text-[#cfc3aa]">
                      nodes {step.factors_tilted.map((f) => f.factor_id).join(', ') || '—'} · gated{' '}
                      {step.contracts_gated.map((c) => c.contract_id).join(', ') || 'none'} · book{' '}
                      {step.book_action}
                    </p>
                    {step.provenance[0]?.claim_id && (
                      <button
                        type="button"
                        className="mono mt-2 inline-flex cursor-pointer text-[10px] text-[#d4a017]"
                        onClick={() => onOpenClaim(step.provenance[0].claim_id!)}
                      >
                        {step.provenance[0].kind} · {step.provenance[0].document} p.
                        {step.provenance[0].page}
                      </button>
                    )}
                  </>
                )}
              </li>
            ))}
          </ol>

          <h3 className="mt-6 text-[16px]">Human-observable watches</h3>
          <ul className="mt-2 space-y-2">
            {world.awaiting_human.map((node) => (
              <li key={node.event_id} className="mono text-[11px] text-[#c9a227]">
                {node.name} — {node.status}
              </li>
            ))}
            {world.awaiting_human.length === 0 && (
              <li className="text-[13px] text-[#9a8b72]">None waiting.</li>
            )}
          </ul>
        </div>
      </div>
    </section>
  )
}
