import {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import { useEffect, useMemo, useState } from 'react'
import type { WorldModel } from '../lib/types'
import { SourceCite } from './SourceCite'

type Props = {
  model: WorldModel
  onOpenClaim: (id: string) => void
}

type WorldNodeData = {
  kind: string
  name: string
  document: string
  page: number
  claimId?: string
  waiting?: boolean
  lit?: boolean
  focused?: boolean
  neighbor?: boolean
}

const NODE_W = 228
const NODE_H = 78
const COL_X = [32, 460, 888]
const ROW_GAP = 128

const nodeTypes = { world: WorldNode }

const MUTED_STROKE = '#6a5c48'
const WORLD_LIT = '#7cb87c'
const FOCUS_LIT = '#d4a017'

function paintNodes(
  nodes: Node<WorldNodeData>[],
  edges: Edge[],
  focusNodeId: string | null,
  focusEdgeId: string | null,
): Node<WorldNodeData>[] {
  const neighborIds = new Set<string>()
  if (focusNodeId) {
    for (const edge of edges) {
      if (edge.source === focusNodeId) neighborIds.add(edge.target)
      if (edge.target === focusNodeId) neighborIds.add(edge.source)
    }
  }
  if (focusEdgeId) {
    const edge = edges.find((item) => item.id === focusEdgeId)
    if (edge) {
      neighborIds.add(edge.source)
      neighborIds.add(edge.target)
    }
  }
  return nodes.map((node) => ({
    ...node,
    data: {
      ...node.data,
      focused: node.id === focusNodeId,
      neighbor: neighborIds.has(node.id),
    },
  }))
}

function paintEdges(
  edges: Edge[],
  focusNodeId: string | null,
  focusEdgeId: string | null,
): Edge[] {
  return edges.map((edge) => {
    const worldLit = Boolean((edge.data as { worldLit?: boolean } | undefined)?.worldLit)
    const focused =
      edge.id === focusEdgeId ||
      (focusNodeId != null && (edge.source === focusNodeId || edge.target === focusNodeId))
    return {
      ...edge,
      type: 'default',
      animated: focused,
      style: {
        stroke: focused ? FOCUS_LIT : worldLit ? WORLD_LIT : MUTED_STROKE,
        strokeWidth: focused ? 2.5 : worldLit ? 2 : 1,
      },
      zIndex: focused ? 4 : worldLit ? 2 : 1,
    }
  })
}

export function GraphView({ model, onOpenClaim }: Props) {
  const [showContracts, setShowContracts] = useState(false)
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null)
  const [focusEdgeId, setFocusEdgeId] = useState<string | null>(null)
  const lit = useMemo(() => new Set(model.lit_node_ids), [model.lit_node_ids])
  const layout = useMemo(() => buildGraph(model, lit), [model, lit])
  const paintedNodes = useMemo(
    () => paintNodes(layout.nodes, layout.edges, focusNodeId, focusEdgeId),
    [layout.nodes, layout.edges, focusNodeId, focusEdgeId],
  )
  const paintedEdges = useMemo(
    () => paintEdges(layout.edges, focusNodeId, focusEdgeId),
    [layout.edges, focusNodeId, focusEdgeId],
  )
  const [nodes, setNodes, onNodesChange] = useNodesState(paintedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(paintedEdges)

  useEffect(() => {
    setFocusNodeId(null)
    setFocusEdgeId(null)
  }, [model.lit_node_ids])

  useEffect(() => {
    setNodes(paintedNodes)
  }, [paintedNodes, setNodes])

  useEffect(() => {
    setEdges(paintedEdges)
  }, [paintedEdges, setEdges])

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-center justify-between gap-4 border-b border-[#3a3226] px-6 py-2">
        <p className="text-[13px] text-[#cfc3aa]">
          Event → factor → exposure. Click a node or edge for the claim. Pan and zoom if the canvas is taller than the pane.
        </p>
        <button
          type="button"
          onClick={() => setShowContracts((v) => !v)}
          className="mono shrink-0 text-[11px] text-[#d4a017]"
        >
          {showContracts ? 'Hide contracts' : 'Show contracts'}
        </button>
      </div>
      <div className="flex min-h-0 flex-1">
        <div className="min-h-0 min-w-0 flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            defaultViewport={{ x: 32, y: 24, zoom: 1 }}
            fitViewOptions={{ padding: 0.18, minZoom: 0.45, maxZoom: 1.2 }}
            minZoom={0.4}
            maxZoom={1.6}
            colorMode="dark"
            nodesConnectable={false}
            defaultEdgeOptions={{ type: 'default' }}
            proOptions={{ hideAttribution: true }}
            onPaneClick={() => {
              setFocusNodeId(null)
              setFocusEdgeId(null)
            }}
            onNodeClick={(_, node) => {
              setFocusNodeId(node.id)
              setFocusEdgeId(null)
              const claimId = node.data.claimId as string | undefined
              if (claimId) onOpenClaim(claimId)
            }}
            onEdgeClick={(_, edge) => {
              setFocusEdgeId(edge.id)
              setFocusNodeId(null)
              const claimId = (edge.data as { claimId?: string } | undefined)?.claimId
              if (claimId) onOpenClaim(claimId)
            }}
          >
            <Background color="#3a3226" gap={22} />
            <Controls />
          </ReactFlow>
        </div>
        {showContracts && (
          <aside className="w-[340px] shrink-0 overflow-y-auto border-l border-[#3a3226] bg-[#1c1812] p-4">
            <h2 className="text-[18px]">Contracts (derived)</h2>
            <ul className="mt-3 space-y-3">
              {model.contracts.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => onOpenClaim(c.claim_id)}
                    className="w-full text-left"
                  >
                    <p className="text-[14px]">{c.name}</p>
                    <p className="mono text-[11px] text-[#9a8b72]">
                      {c.metric} · {c.threshold}
                    </p>
                    <p className="mt-1">
                      <SourceCite document={c.document} page={c.page} />
                    </p>
                    <p className="mono mt-1 text-[10px] text-[#d4a017]">
                      {c.kill_switch ? 'KILL SWITCH' : 'SOURCE-BACKED'}
                      {lit.has(c.id) ? ' · LIT' : ''}
                    </p>
                  </button>
                </li>
              ))}
              {model.policies.map((p) => (
                <li key={p.id} className="border-t border-[#3a3226] pt-3">
                  <p className="mono text-[10px] text-[#c45c26]">OUR POLICY</p>
                  <p className="text-[14px]">{p.name}</p>
                  <p className="mt-1">
                    <SourceCite document={p.document} page={p.page} />
                  </p>
                  <p className="mt-1 text-[12px] text-[#cfc3aa]">{p.text}</p>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </div>
  )
}

function WorldNode({ data }: NodeProps<Node<WorldNodeData>>) {
  const lit = Boolean(data.lit)
  const waiting = Boolean(data.waiting)
  const focused = Boolean(data.focused)
  const neighbor = Boolean(data.neighbor)
  const borderColor = focused
    ? FOCUS_LIT
    : neighbor
      ? WORLD_LIT
      : waiting
        ? '#c9a227'
        : lit
          ? WORLD_LIT
          : '#3a3226'
  return (
    <div
      className="h-full rounded-sm border px-2.5 py-2"
      style={{
        width: NODE_W,
        height: NODE_H,
        background: '#241e16',
        borderColor,
        boxShadow: focused ? '0 0 0 1px #d4a017' : undefined,
      }}
    >
      <Handle type="target" position={Position.Left} className="!h-2 !w-2 !bg-[#9a8b72]" />
      <p className="mono text-[10px] leading-none tracking-[0.08em] text-[#9a8b72]">
        {data.kind}
        {lit ? ' · LIT' : ''}
      </p>
      <p className="mt-1 line-clamp-2 text-[12px] leading-snug text-[#e8dcc4]">{data.name}</p>
      <p className="mt-1">
        <SourceCite document={data.document} page={data.page} />
      </p>
      <Handle type="source" position={Position.Right} className="!h-2 !w-2 !bg-[#9a8b72]" />
    </div>
  )
}

function buildGraph(model: WorldModel, lit: Set<string>): { nodes: Node<WorldNodeData>[]; edges: Edge[] } {
  const nodes: Node<WorldNodeData>[] = []
  const edges: Edge[] = []
  const deepFactors = model.factors.filter((f) => f.deep)
  const deepIds = new Set(deepFactors.map((f) => f.id))
  const liveRels = model.relationships.filter((r) => deepIds.has(r.factor_id))
  const eventIds = new Set(liveRels.map((r) => r.event_id))
  const events = model.events.filter((e) => eventIds.has(e.id))
  const liveExps = model.exposures.filter((e) => deepIds.has(e.factor_id))
  const tickers = [...new Set(liveExps.map((e) => e.ticker))]

  events.forEach((event, i) => {
    const kind =
      event.observability === 'human_observable'
        ? 'HUMAN'
        : event.third_party
          ? '3RD PARTY'
          : 'MACHINE'
    nodes.push({
      id: event.id,
      type: 'world',
      position: { x: COL_X[0], y: 16 + i * ROW_GAP },
      style: { width: NODE_W, height: NODE_H },
      data: {
        kind,
        name: event.name,
        document: event.document,
        page: event.page,
        waiting: event.observability === 'human_observable',
        lit: lit.has(event.id),
        claimId: liveRels.find((r) => r.event_id === event.id)?.claim_id ?? undefined,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    })
  })

  deepFactors.forEach((factor, i) => {
    const tilt = model.factor_tilts[factor.id] ?? 'unresolved'
    nodes.push({
      id: factor.id,
      type: 'world',
      position: { x: COL_X[1], y: 16 + i * ROW_GAP },
      style: { width: NODE_W, height: NODE_H },
      data: {
        kind: `FACTOR · ${tilt}`,
        name: factor.name,
        document: factor.document,
        page: factor.page,
        lit: lit.has(factor.id),
        claimId: liveRels.find((r) => r.factor_id === factor.id)?.claim_id ?? undefined,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    })
  })

  tickers.forEach((ticker, i) => {
    const exp = liveExps.find((e) => e.ticker === ticker)
    const named = model.tickers.find((t) => t.symbol === ticker)
    nodes.push({
      id: `TK-${ticker}`,
      type: 'world',
      position: { x: COL_X[2], y: 16 + i * ROW_GAP },
      style: { width: NODE_W, height: NODE_H },
      data: {
        kind: exp?.has_position_policy ? 'BOOK' : 'EXPOSURE ONLY',
        name: ticker,
        document: named?.document ?? exp?.document ?? '',
        page: named?.page ?? exp?.page ?? 0,
        lit: lit.has(ticker),
        claimId: exp?.claim_id ?? undefined,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    })
  })

  liveRels.forEach((rel) => {
    edges.push({
      id: rel.id,
      source: rel.event_id,
      target: rel.factor_id,
      type: 'default',
      label: rel.direction,
      style: { stroke: MUTED_STROKE, strokeWidth: 1 },
      labelStyle: { fill: '#e8dcc4', fontSize: 11, fontFamily: 'IBM Plex Mono, ui-monospace, monospace' },
      labelBgStyle: { fill: '#14110c' },
      labelBgPadding: [6, 3],
      labelBgBorderRadius: 2,
      data: { claimId: rel.claim_id, worldLit: lit.has(rel.id) },
    })
  })

  liveExps.forEach((exp) => {
    edges.push({
      id: exp.id,
      source: exp.factor_id,
      target: `TK-${exp.ticker}`,
      type: 'default',
      style: { stroke: MUTED_STROKE, strokeWidth: 1 },
      data: { claimId: exp.claim_id, worldLit: lit.has(exp.id) },
    })
  })

  return { nodes, edges }
}
