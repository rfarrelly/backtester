export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type DatasetSummary = {
  dataset_id: string;
  filename: string;
  created_at: string | null;
};

export type DatasetIntrospection = {
  dataset_id: string;
  filename: string;
  columns: string[];
  inferred_types: Record<string, string>;
  sample_rows: Record<string, string | null>[];
};

export type DatasetMapping = {
  home_team_col: string;
  away_team_col: string;
  date_col: string;
  time_col?: string | null;

  date_format?: string | null;
  time_format?: string | null;

  league_col?: string | null;
  season_col?: string | null;

  result_col?: string | null;
  home_goals_col?: string | null;
  away_goals_col?: string | null;

  odds_home_col?: string | null;
  odds_draw_col?: string | null;
  odds_away_col?: string | null;

  model_home_prob_col?: string | null;
  model_draw_prob_col?: string | null;
  model_away_prob_col?: string | null;

  feature_cols: string[];
};

export type DayKey = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export type CustomPeriodDefinition = {
  name: string;
  start_day: DayKey;
  end_day: DayKey;
};

export type SimulationRequest = {
  league?: string | null;
  leagues?: string[] | null;
  season: string;

  selection?: "H" | "D" | "A" | null;
  rule_expression?: string | null;

  staking_method: "fixed" | "percent" | "kelly";
  fixed_stake?: number | null;
  percent_stake?: number | null;
  kelly_fraction?: number | null;

  starting_bankroll: number;
  multiple_legs: number;

  min_odds?: number | null;

  walk_forward?: boolean;
  train_window_matches?: number | null;
  test_window_matches?: number | null;
  step_matches?: number | null;

  period_mode?: "none" | "custom";
  custom_periods?: CustomPeriodDefinition[] | null;
  reset_bankroll_each_period?: boolean;

  max_candidates_per_period?: number | null;
  rank_by?: string | null;
  rank_order?: "asc" | "desc";
  require_full_candidate_count?: boolean;
};

export type DatasetSimulateRequest = {
  mapping: DatasetMapping;
  request: SimulationRequest;
  persist: boolean;
};

export type RuleValidateRequest = {
  expression: string;
  available_names?: string[];
  sample_vars?: Record<string, unknown> | null;
};

export type RuleValidateResponse = {
  ok: true;
  expression: string;
  used_names: string[];
  unknown_names: string[];
  error: null;
};

export type EquityPoint = {
  t?: string | null;
  bankroll: number;
  segment_index?: number;
  period_index?: number;
  period_label?: string;
};

export type BetLeg = {
  match_id: string;
  kickoff: string;
  home_team: string;
  away_team: string;
  result: string;
  selection: string;
  odds?: number | null;
  implied_prob?: number | null;
  model_prob?: number | null;
  edge?: number | null;
  features?: Record<string, unknown>;
  league?: string | null;
};

export type BetResult = {
  stake: number;
  combined_odds: number;
  is_win: boolean;
  profit: number;
  return_amount: number;
  settled_at?: string | null;
  legs: BetLeg[];
  meta?: Record<string, unknown>;
};

export type WalkForwardSegment = {
  segment_index: number;
  train_start_kickoff?: string | null;
  train_end_kickoff?: string | null;
  test_start_kickoff?: string | null;
  test_end_kickoff?: string | null;
  roi_percent: number;
  total_bets: number;
  final_bankroll: number;
};

export type SimulationResult = {
  run_id: string | null;
  dataset_id: string;
  final_bankroll: number;
  roi_percent: number;
  total_bets: number;
  total_wins?: number;
  total_losses?: number;
  strike_rate_percent?: number;
  max_drawdown_percent?: number;
  profit_factor?: number | null;
  average_odds?: number | null;
  total_profit?: number | null;
  bets: BetResult[];
  equity_curve?: EquityPoint[];
  available_features?: string[];

  walk_forward?: boolean;
  total_segments?: number;
  segments?: WalkForwardSegment[];

  calendar_periods?: boolean;
  period_mode?: "none" | "custom";
  total_periods?: number;
  periods?: CalendarPeriodSummary[];
};

export type RunSummary = {
  run_id: string;
  dataset_id: string;
  created_at: string | null;
  roi_percent: number | null;
  final_bankroll: number | null;
  total_bets: number | null;
  max_drawdown_percent: number | null;
};

export type RunDetail = {
  run_id: string;
  dataset_id: string;
  created_at: string | null;
  mapping: DatasetMapping;
  request: SimulationRequest;
  result: SimulationResult;
};

export type CalendarPeriodSummary = {
  period_index: number;
  period_label: string;
  start_kickoff: string;
  end_kickoff: string;
  starting_bankroll: number;
  final_bankroll: number;
  roi_percent: number;
  total_bets: number;
  total_wins?: number;
  total_losses?: number;
  strike_rate_percent?: number;
  max_drawdown_percent?: number | null;
  profit_factor?: number | null;
  matches_in_period?: number;
  eligible_candidates?: number;
  selected_candidates?: number;
  bets_created?: number;
};

export type DatasetSweepRequest = {
  mapping: DatasetMapping;
  base_request: SimulationRequest;
  grid: Record<string, unknown[]>;
  persist_runs: boolean;
};

export type SweepVariantResult = {
  params: Record<string, unknown>;
  run_id?: string | null;
  roi_percent: number;
  final_bankroll: number;
  total_bets: number;
  max_drawdown_percent?: number | null;
  strike_rate_percent?: number | null;
  profit_factor?: number | null;
  average_odds?: number | null;
  total_profit?: number | null;
};

export type DatasetSweepResponse = {
  total_variants: number;
  results: SweepVariantResult[];
};
