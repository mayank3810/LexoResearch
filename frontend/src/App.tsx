import { useEffect, useState } from 'react'
import { AsOfStrip } from './components/AsOfStrip'
import { ClaimDrawer } from './components/ClaimDrawer'
import { GraphView } from './components/GraphView'
import { ThesisView } from './components/ThesisView'
import { WorkbenchView } from './components/WorkbenchView'
import { api } from './lib/api'
import type { AsOf, CalendarItem, Claim, Thesis, WorldModel, WorldSnapshot } from './lib/types'

type View = 'thesis' | 'graph' | 'workbench'

export default function App() {
  const [view, setView] = useState<View>('thesis')
  const [asOf, setAsOf] = useState<AsOf | null>(null)
  const [model, setModel] = useState<WorldModel | null>(null)
  const [calendar, setCalendar] = useState<CalendarItem[]>([])
  const [worldA, setWorldA] = useState<WorldSnapshot | null>(null)
  const [worldB, setWorldB] = useState<WorldSnapshot | null>(null)
  const [asOfThesis, setAsOfThesis] = useState<Thesis | null>(null)
  const [claim, setClaim] = useState<Claim | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [graphWorld, setGraphWorld] = useState<'ASOF' | 'A' | 'B'>('ASOF')

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.asOf(),
      api.worldModel(),
      api.calendar(),
      api.world('A'),
      api.world('B'),
      api.thesis('ASOF'),
    ])
      .then(([asOfBody, modelBody, calendarBody, a, b, asof]) => {
        if (cancelled) return
        setAsOf(asOfBody)
        setModel(modelBody)
        setCalendar(calendarBody.items)
        setWorldA(a)
        setWorldB(b)
        setAsOfThesis(asof.thesis)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function openClaim(id: string) {
    setClaim(await api.claim(id))
  }

  async function refreshGraph(world: 'ASOF' | 'A' | 'B') {
    setGraphWorld(world)
    const base = await api.worldModel()
    const live = world === 'A' ? worldA : world === 'B' ? worldB : null
    if (live) {
      setModel({
        ...base,
        lit_node_ids: live.lit_node_ids,
        factor_tilts: live.factor_tilts,
      })
      return
    }
    setModel(base)
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-[#c44c3a]">Cannot reach the engine. If this is local, start the backend on :8000.</p>
        <p className="mono mt-2 text-[12px] text-[#9a8b72]">{error}</p>
      </div>
    )
  }

  if (!asOf || !model || !worldA || !worldB || !asOfThesis) {
    return <p className="p-8 text-[#9a8b72]">Loading the compiled world…</p>
  }

  return (
    <div className={view === 'graph' ? 'flex h-svh flex-col overflow-hidden' : 'min-h-svh'}>
      <AsOfStrip asOf={asOf} />
      <nav className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-[#3a3226] px-6">
        <div className="flex gap-6">
          {(
            [
              ['thesis', 'Thesis-state'],
              ['graph', 'World graph'],
              ['workbench', 'Workbench'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={async () => {
                setView(id)
                if (id === 'graph') await refreshGraph(graphWorld)
              }}
              className={`mono py-3 text-[12px] tracking-[0.12em] uppercase ${
                view === id ? 'text-[#d4a017]' : 'text-[#9a8b72]'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {view === 'graph' && (
          <div className="mono flex gap-3 text-[11px] text-[#9a8b72]">
            {(['ASOF', 'A', 'B'] as const).map((id) => (
              <button
                key={id}
                type="button"
                onClick={() => refreshGraph(id)}
                className={graphWorld === id ? 'text-[#d4a017]' : ''}
              >
                {id === 'ASOF' ? 'as-of' : `world ${id}`}
              </button>
            ))}
          </div>
        )}
      </nav>

      {view === 'thesis' && (
        <ThesisView thesis={asOfThesis} model={model} onOpenClaim={openClaim} />
      )}
      {view === 'graph' && (
        <div className="min-h-0 flex-1">
          <GraphView model={model} onOpenClaim={openClaim} />
        </div>
      )}
      {view === 'workbench' && (
        <WorkbenchView
          calendar={calendar}
          worldA={worldA}
          worldB={worldB}
          onChange={(id, next) => {
            if (id === 'A') setWorldA(next)
            else setWorldB(next)
          }}
          onOpenClaim={openClaim}
        />
      )}

      <ClaimDrawer
        claim={claim}
        provenance={claim ? 'source_backed' : 'our_policy'}
        onClose={() => setClaim(null)}
      />
    </div>
  )
}
