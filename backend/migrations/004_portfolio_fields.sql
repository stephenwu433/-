-- Portfolio / richer project setup fields (align with reference MVP)

ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS objective TEXT,
    ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES users (id),
    ADD COLUMN IF NOT EXISTS member_daily_hours NUMERIC(5, 1) NOT NULL DEFAULT 6.0,
    ADD COLUMN IF NOT EXISTS plan_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_projects_owner_user_id ON projects (owner_user_id);
