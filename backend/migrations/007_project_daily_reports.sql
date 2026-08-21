-- Optional narrative overrides for auto-generated project daily reports

CREATE TABLE IF NOT EXISTS project_daily_reports (
    id UUID PRIMARY KEY,
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    summary_text TEXT,
    next_actions TEXT,
    created_by_user_id UUID NOT NULL REFERENCES users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_project_daily_reports_project_date UNIQUE (project_id, report_date)
);

CREATE INDEX IF NOT EXISTS idx_project_daily_reports_project_date
    ON project_daily_reports (project_id, report_date);
