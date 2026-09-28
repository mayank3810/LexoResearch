import type { AsOf } from '../lib/types'
import { SourceCite } from './SourceCite'

export function AsOfStrip({ asOf }: { asOf: AsOf }) {
  return (
    <header className="border-b border-[#3a3226] bg-[#1c1812] px-6 py-3">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mono text-[11px] tracking-[0.18em] text-[#9a8b72] uppercase">
            Lexo world model · NVDA instance
          </p>
          <h1 className="mt-1 text-[28px] leading-none text-[#e8dcc4]">NVIDIA — live thesis-state</h1>
          <p className="mt-2">
            <SourceCite document={asOf.document} page={asOf.page} className="mono text-[11px] text-[#9a8b72]" />
          </p>
        </div>
        <dl className="mono grid grid-cols-2 gap-x-6 gap-y-1 text-[12px] sm:grid-cols-5">
          <div>
            <dt className="text-[#9a8b72]">Price</dt>
            <dd>${asOf.price.toFixed(2)}</dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">Rating</dt>
            <dd>{asOf.rating}</dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">Conviction</dt>
            <dd>{asOf.conviction} <span className="text-[#9a8b72]">sourced</span></dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">Position</dt>
            <dd>{asOf.position}</dd>
          </div>
          <div>
            <dt className="text-[#9a8b72]">As-of</dt>
            <dd>{asOf.memo_date}</dd>
          </div>
        </dl>
      </div>
    </header>
  )
}
