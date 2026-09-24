PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS company_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL DEFAULT 'discovery',
    strategy_mode TEXT NOT NULL DEFAULT 'distribution_first',
    objective_version TEXT NOT NULL,
    available_capital_usd REAL NOT NULL DEFAULT 0,
    committed_capital_usd REAL NOT NULL DEFAULT 0,
    last_reconciled_at TEXT
);

CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    state TEXT NOT NULL,
    thesis TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audiences (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT,
    name TEXT NOT NULL,
    target_customer TEXT NOT NULL,
    painful_job TEXT,
    qualification_definition TEXT,
    estimated_value_tier TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS distribution_assets (
    id TEXT PRIMARY KEY,
    audience_id TEXT NOT NULL,
    opportunity_id TEXT,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    source_channel TEXT,
    owned_or_rented TEXT NOT NULL CHECK (owned_or_rented IN ('owned','rented','hybrid')),
    monthly_reach INTEGER NOT NULL DEFAULT 0,
    qualified_users INTEGER NOT NULL DEFAULT 0,
    repeat_users INTEGER NOT NULL DEFAULT 0,
    permissioned_contacts INTEGER NOT NULL DEFAULT 0,
    acquisition_cost_usd REAL,
    organic_share REAL,
    engagement_rate REAL,
    commercial_intent_rate REAL,
    status TEXT NOT NULL DEFAULT 'testing',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (audience_id) REFERENCES audiences(id),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS commercial_signals (
    id TEXT PRIMARY KEY,
    audience_id TEXT,
    distribution_asset_id TEXT,
    opportunity_id TEXT,
    signal_type TEXT NOT NULL,
    signal_strength INTEGER NOT NULL DEFAULT 1 CHECK (signal_strength BETWEEN 1 AND 5),
    source TEXT,
    evidence_id TEXT,
    observed_at TEXT NOT NULL,
    FOREIGN KEY (audience_id) REFERENCES audiences(id),
    FOREIGN KEY (distribution_asset_id) REFERENCES distribution_assets(id),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT,
    venture_id TEXT,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    owner_role TEXT NOT NULL,
    state TEXT NOT NULL,
    budget_cap_usd REAL NOT NULL DEFAULT 0,
    actual_cost_usd REAL NOT NULL DEFAULT 0,
    success_criteria TEXT NOT NULL,
    failure_criteria TEXT NOT NULL,
    stop_conditions TEXT,
    started_at TEXT,
    ended_at TEXT,
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    hypothesis_id TEXT,
    experiment_id TEXT,
    level INTEGER NOT NULL CHECK (level BETWEEN 0 AND 7),
    kind TEXT NOT NULL,
    source TEXT,
    artifact_path TEXT,
    verified INTEGER NOT NULL DEFAULT 0,
    observed_at TEXT NOT NULL,
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    actor_role TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    rationale TEXT NOT NULL,
    evidence_refs TEXT,
    budget_usd REAL NOT NULL DEFAULT 0,
    stop_condition TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger (
    id TEXT PRIMARY KEY,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('revenue','expense','commitment','transfer')),
    amount_usd REAL NOT NULL,
    counterparty TEXT,
    experiment_id TEXT,
    venture_id TEXT,
    evidence_id TEXT,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    asset_type TEXT NOT NULL,
    name TEXT NOT NULL,
    location TEXT,
    replacement_cost_usd REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risks (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    state TEXT NOT NULL,
    owner_role TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_audit (
    id TEXT PRIMARY KEY,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    policy_decision TEXT NOT NULL,
    external_ref TEXT,
    created_at TEXT NOT NULL
);
