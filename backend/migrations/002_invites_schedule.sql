-- PlanFlow step: member invites + project schedule dates
-- 小白说明：
-- 1) team_invites     = 邀请链接（别人点开链接并登录后加入团队）
-- 2) projects 增加 planned_start / planned_end = 排期起止日期

ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS planned_start DATE,
    ADD COLUMN IF NOT EXISTS planned_end DATE;

CREATE TABLE IF NOT EXISTS team_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('admin', 'member')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'revoked')),
    invited_by_user_id UUID NOT NULL REFERENCES users (id),
    accepted_by_user_id UUID REFERENCES users (id),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_team_invites_team_id ON team_invites (team_id);
CREATE INDEX IF NOT EXISTS idx_team_invites_token ON team_invites (token);
CREATE INDEX IF NOT EXISTS idx_projects_planned_start ON projects (planned_start);
