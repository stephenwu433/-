-- Project-scoped members (reference MVP: members belong to a project with a job title).
-- Also day-completion fields on daily reports for the daily-tasks feedback slider.

CREATE TABLE IF NOT EXISTS project_members (
    id UUID PRIMARY KEY,
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    job_title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_project_members_project_user UNIQUE (project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members (project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_team_id ON project_members (team_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members (user_id);

-- Backfill: every current team member becomes a project member on that team's projects.
INSERT INTO project_members (id, team_id, project_id, user_id, job_title, created_at)
SELECT gen_random_uuid(),
       p.team_id,
       p.id,
       tm.user_id,
       tm.job_title,
       now()
FROM projects p
JOIN team_members tm ON tm.team_id = p.team_id
ON CONFLICT (project_id, user_id) DO NOTHING;

ALTER TABLE project_daily_reports
    ADD COLUMN IF NOT EXISTS completion_percent INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS day_note TEXT;

-- Keep completion in 0..100
ALTER TABLE project_daily_reports
    DROP CONSTRAINT IF EXISTS chk_project_daily_reports_completion;
ALTER TABLE project_daily_reports
    ADD CONSTRAINT chk_project_daily_reports_completion
    CHECK (completion_percent >= 0 AND completion_percent <= 100);
