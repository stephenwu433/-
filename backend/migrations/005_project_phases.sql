-- Project cycle schedule: phases + work items under a project

CREATE TABLE IF NOT EXISTS project_phases (
    id UUID PRIMARY KEY,
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    planned_start DATE,
    planned_end DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_phases_project_id ON project_phases (project_id);

CREATE TABLE IF NOT EXISTS phase_work_items (
    id UUID PRIMARY KEY,
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    phase_id UUID NOT NULL REFERENCES project_phases (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    assignee_user_id UUID REFERENCES users (id),
    planned_start DATE,
    planned_end DATE,
    estimated_hours NUMERIC(8, 1) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'todo',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_phase_work_items_project_id ON phase_work_items (project_id);
CREATE INDEX IF NOT EXISTS idx_phase_work_items_phase_id ON phase_work_items (phase_id);
