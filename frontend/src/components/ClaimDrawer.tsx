import type { Claim } from '../lib/types'

export function ClaimDrawer({
  claim,
  policyText,
  provenance,
  observability,
  onClose,
}: {
  claim: Claim | null
  policyText?: string | null
  provenance: string
  observability?: string
  onClose: () => void
}) {
  if (!claim && !policyText) return null
  const painted =
    provenance === 'our_policy' || provenance === 'ours_no_claim'
  return (
    <aside className="fixed inset-y-0 right-0 z-20 w-full max-w-md overflow-y-auto border-l border-[#3a3226] bg-[#241e16] p-6 shadow-2xl">
      <div className="flex items-start justify-between gap-4">
        <p className="mono text-[11px] tracking-[0.16em] uppercase text-[#9a8b72]">
          Provenance
        </p>
        <button type="button" onClick={onClose} className="mono text-[12px] text-[#9a8b72]">
          Close
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <span
          className={`mono rounded-sm px-2 py-1 text-[11px] ${
            painted
              ? 'bg-[#c45c26]/20 text-[#e8b089]'
              : 'bg-[#d4a017]/15 text-[#d4a017]'
          }`}
        >
          {painted ? 'OUR POLICY' : 'SOURCE-BACKED'}
        </span>
        {observability && (
          <span className="mono rounded-sm bg-[#14110c] px-2 py-1 text-[11px] text-[#c9a227]">
            {observability}
          </span>
        )}
      </div>
      {claim && (
        <>
          <h2 className="mt-5 text-[22px]">{claim.text}</h2>
          <p className="mono mt-3 text-[12px] text-[#9a8b72]">
            {claim.document} · p.{claim.page} · {claim.section}
          </p>
          <blockquote className="mt-4 border-l-2 border-[#d4a017] pl-4 text-[15px] leading-relaxed text-[#e8dcc4]">
            {claim.quote}
          </blockquote>
        </>
      )}
      {policyText && (
        <p className="mt-5 text-[15px] leading-relaxed text-[#e8b089]">{policyText}</p>
      )}
    </aside>
  )
}
