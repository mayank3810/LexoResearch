export type PdfSource = {
  document: string
  page: number
}

export type Claim = PdfSource & {
  id: string
  text: string
  section: string
  quote: string
}

export type AsOf = PdfSource & {
  date: string
  ticker: string
  price: number
  rating: string
  conviction: string
  conviction_note: string
  position: string
  memo_date: string
  fy2028: PdfSource & {
    workbook_revenue_m: number
    workbook_growth_pct: number
    management_guide_pct: number
    consensus_revenue_m: number
    note: string
    claim_id: string
  }
  banner: string
}

export type Thesis = {
  world_id: string
  scenario: 'BULL' | 'BASE' | 'BEAR'
  rating: 'Hold' | 'Buy' | 'Sell'
  conviction: string
  unresolved_factors: string[]
  position: 'none' | 'long'
  position_action: string
  starting_book: 'flat' | 'long'
  override_active: boolean
  kill_switch_up: boolean
  kill_switch_ids: string[]
  fy2028_row: AsOf['fy2028']
  notes: string[]
}

export type LedgerStep = {
  seq: number
  date: string
  event_id: string
  event_name: string
  outcome: string
  entity: string
  third_party: boolean
  factors_tilted: Array<Record<string, string>>
  exposures_lit: Array<Record<string, string | boolean>>
  contracts_gated: Array<Record<string, string | boolean>>
  thesis_before: Thesis
  thesis_after: Thesis
  book_action: string
  provenance: Array<{
    kind: string
    claim_id: string | null
    policy_id: string | null
    document: string | null
    page: number | null
    section: string | null
    quote: string | null
  }>
  skipped: boolean
  skip_reason: string | null
}

export type WorldSnapshot = {
  world_id: string
  banner: string
  starting_book: 'flat' | 'long'
  thesis: Thesis
  factor_tilts: Record<string, string>
  lit_node_ids: string[]
  awaiting_human: Array<{
    event_id: string
    name: string
    status: string
    bound: boolean
  }>
  ledger: LedgerStep[]
  tape_hash: string
  bindings: Array<{
    event_id: string
    outcome: string
    date: string | null
    adjudicated: boolean
  }>
}

export type CalendarItem = PdfSource & {
  id: string
  event_id: string
  date: string
  label: string
  unresolved: boolean
  event: PdfSource & {
    id: string
    name: string
    entity: string
    possible_outcomes: string[]
    observability: string
    third_party: boolean
    description: string
  }
}

export type WorldModel = {
  banner: string
  as_of: AsOf
  tickers: Array<PdfSource & { symbol: string; name: string; role: string }>
  factors: Array<
    PdfSource & {
      id: string
      name: string
      circle: string
      force_type: string
      impact: number | null
      theme_weight: number | null
      description: string
      deep: boolean
    }
  >
  events: Array<
    PdfSource & {
      id: string
      name: string
      entity: string
      observability: string
      possible_outcomes: string[]
      third_party: boolean
      description: string
      date: string | null
    }
  >
  relationships: Array<
    PdfSource & {
      id: string
      event_id: string
      outcome: string
      factor_id: string
      direction: string
      provenance: string
      claim_id: string | null
      policy_id: string | null
      note: string
    }
  >
  exposures: Array<
    PdfSource & {
      id: string
      ticker: string
      factor_id: string
      has_position_policy: boolean
      note: string
      claim_id: string | null
    }
  >
  contracts: Array<
    PdfSource & {
      id: string
      name: string
      kind: string
      metric: string
      threshold: string
      timeframe: string
      gates: string
      provenance: string
      claim_id: string
      kill_switch: boolean
      holders_only: boolean
    }
  >
  policies: Array<
    PdfSource & {
      id: string
      name: string
      provenance: string
      text: string
      retires_when: string | null
      claim_id: string | null
    }
  >
  scenarios: Array<
    PdfSource & {
      id: string
      name: string
      probability_pct: number
      region: string
      claim_id: string
    }
  >
  lit_node_ids: string[]
  factor_tilts: Record<string, string>
}
