PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS company_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL DEFAULT 'discovery',
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
