import type { Thesis, WorldModel } from '../lib/types'
import { SourceCite } from './SourceCite'

const scenarioTone: Record<Thesis['scenario'], string> = {
  BULL: 'text-[#5a9e6f]',
  BASE: 'text-[#d4a017]',
  BEAR: 'text-[#c44c3a]',
}

export function ThesisView({
  thesis,
  model,
  onOpenClaim,
}: {
  thesis: Thesis
  model: WorldModel
  onOpenClaim: (id: string) => void
}) {
  const unresolved = thesis.unresolved_factors
    .map((id) => model.factors.find((f) => f.id === id))
    .filter(Boolean)

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-6 py-8">
        <p className="text-[14px] text-[#9a8b72]">
          How the research reads as of 8 September 2026, before any later print is bound. Use the workbench to run World A and World B against this same model.
        </p>
      <section className="grid gap-6 md:grid-cols-4">
        <StateCard label="Scenario" value={thesis.scenario} className={scenarioTone[thesis.scenario]} />
        <StateCard label="Rating" value={thesis.rating} />
        <StateCard label="Position" value={thesis.position} />
        <StateCard label="Action" value={thesis.position_action} />
      </section>

      <section className="border border-[#3a3226] bg-[#1c1812] p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-[22px]">The one-row FY2028 disagreement</h2>
            <p className="mt-1">
              <SourceCite document={thesis.fy2028_row.document} page={thesis.fy2028_row.page} />
            </p>
          </div>
          <button
            type="button"
            className="mono text-[11px] text-[#d4a017]"
            onClick={() => onOpenClaim(thesis.fy2028_row.claim_id)}
          >
            Open claim
          </button>
        </div>
        <p className="mt-2 max-w-3xl text-[15px] text-[#cfc3aa]">{thesis.fy2028_row.note}</p>
        <dl className="mono mt-4 grid grid-cols-2 gap-4 text-[12px] sm:grid-cols-4">
          <div>
            <dt className="text-[#9a8b72]">Workbook FY2028</dt>
            <dd>${thesis.fy2028_row.workbook_revenue_m.toLocaleString()}M</dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">Workbook growth</dt>
            <dd>{thesis.fy2028_row.workbook_growth_pct}%</dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">Management guide</dt>
            <dd>~{thesis.fy2028_row.management_guide_pct}%</dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">Consensus</dt>
            <dd>${thesis.fy2028_row.consensus_revenue_m.toLocaleString()}M</dd>
          </div>
        </dl>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="border border-[#3a3226] bg-[#1c1812] p-5">
          <h2 className="text-[20px]">Unresolved deep factors</h2>
          <ul className="mt-3 space-y-2 text-[14px]">
            {unresolved.length === 0 && <li className="text-[#9a8b72]">None on the deep path.</li>}
            {unresolved.map((f) => (
              <li key={f!.id} className="flex justify-between gap-3">
                <span>
                  {f!.name}
                  <span className="mt-0.5 block">
                    <SourceCite document={f!.document} page={f!.page} />
                  </span>
                </span>
                <span className="mono text-[11px] text-[#9a8b72]">{f!.id}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="border border-[#3a3226] bg-[#1c1812] p-5">
          <h2 className="text-[20px]">Gates and paint</h2>
          <ul className="mt-3 space-y-3 text-[14px]">
            <li>
              Neutral-spring override:{' '}
              <span className={thesis.override_active ? 'text-[#c45c26]' : 'text-[#5a9e6f]'}>
                {thesis.override_active ? 'ACTIVE — our policy' : 'retired'}
              </span>
            </li>
            <li>
              Kill switch:{' '}
              <span className={thesis.kill_switch_up ? 'text-[#c44c3a]' : 'text-[#9a8b72]'}>
                {thesis.kill_switch_up ? thesis.kill_switch_ids.join(', ') : 'down'}
              </span>
            </li>
            <li>Conviction stays {thesis.conviction} because the memo named it. No score invented.</li>
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-[20px]">All 28 named factors</h2>
        <p className="mt-1 text-[13px] text-[#9a8b72]">
          Named forces from the memo. A weight is how large the research said that force is.
        </p>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {model.factors
            .filter((f) => f.id.startsWith('F-') && !['F-FY2028', 'F-NVDA-DEMAND'].includes(f.id))
            .map((f) => (
              <div key={f.id} className="border border-[#3a3226] px-3 py-2">
                <p className="mono text-[10px] text-[#9a8b72]">
                  {f.id} · {f.circle} · {f.force_type}
                  {f.impact != null ? ` · impact ${f.impact}` : ''}
                  {f.theme_weight != null ? ` · w${f.theme_weight}` : ''}
                </p>
                <p className="text-[13px]">{f.name}</p>
                <p className="mt-1">
                  <SourceCite document={f.document} page={f.page} />
                </p>
              </div>
            ))}
        </div>
      </section>

      <section>
        <h2 className="text-[20px]">Scenario regions the research named</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {model.scenarios.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onOpenClaim(s.claim_id)}
              className={`border p-4 text-left ${
                s.name === thesis.scenario ? 'border-[#d4a017] bg-[#241e16]' : 'border-[#3a3226] bg-[#1c1812]'
              }`}
            >
              <p className="mono text-[11px] text-[#9a8b72]">{s.probability_pct}% sourced</p>
              <p className="mt-1 text-[18px]">{s.name}</p>
              <p className="mt-2 text-[13px] text-[#cfc3aa]">{s.region}</p>
              <p className="mt-2">
                <SourceCite document={s.document} page={s.page} />
              </p>
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}

function StateCard({
  label,
  value,
  className = '',
}: {
  label: string
  value: string
  className?: string
}) {
  return (
    <div className="border border-[#3a3226] bg-[#1c1812] px-4 py-5">
      <p className="mono text-[11px] tracking-[0.14em] text-[#9a8b72] uppercase">{label}</p>
      <p className={`mt-2 text-[28px] leading-none ${className}`}>{value}</p>
    </div>
  )
}

