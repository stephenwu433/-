-- Daily hours logging against tasks

CREATE TABLE IF NOT EXISTS task_time_entries (
    id UUID PRIMARY KEY,
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    work_date DATE NOT NULL,
    hours NUMERIC(6, 1) NOT NULL DEFAULT 0,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_task_time_entries_task_user_date UNIQUE (task_id, user_id, work_date)
);

CREATE INDEX IF NOT EXISTS idx_task_time_entries_project_date
    ON task_time_entries (project_id, work_date);

CREATE INDEX IF NOT EXISTS idx_task_time_entries_user_date
    ON task_time_entries (user_id, work_date);
