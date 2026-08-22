-- Link cycle schedule work items to concrete project tasks

ALTER TABLE phase_work_items
    ADD COLUMN IF NOT EXISTS task_id UUID REFERENCES tasks (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_phase_work_items_task_id ON phase_work_items (task_id);
