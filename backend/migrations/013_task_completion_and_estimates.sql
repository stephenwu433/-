-- Persist per-task day completion and planned daily hours for workload parity.

ALTER TABLE task_time_entries
    ADD COLUMN IF NOT EXISTS completion_percent INTEGER NOT NULL DEFAULT 0;

ALTER TABLE task_time_entries
    DROP CONSTRAINT IF EXISTS chk_task_time_entries_completion;
ALTER TABLE task_time_entries
    ADD CONSTRAINT chk_task_time_entries_completion
    CHECK (completion_percent >= 0 AND completion_percent <= 100);

ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS estimated_hours NUMERIC(8, 1) NOT NULL DEFAULT 0;
