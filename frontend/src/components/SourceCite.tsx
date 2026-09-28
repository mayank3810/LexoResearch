export function SourceCite({
  document,
  page,
  className = 'mono text-[10px] text-[#9a8b72]',
}: {
  document: string
  page: number
  className?: string
}) {
  return (
    <span className={className}>
      {document} · p.{page}
    </span>
  )
}
