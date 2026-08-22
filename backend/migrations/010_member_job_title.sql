-- Add job position (岗位) for team members — separate from permission role

ALTER TABLE team_members
    ADD COLUMN IF NOT EXISTS job_title TEXT;

CREATE INDEX IF NOT EXISTS idx_team_members_job_title ON team_members (job_title);
