-- Expand task status values to match reference MVP.
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_status_check;
ALTER TABLE tasks
    ADD CONSTRAINT tasks_status_check
    CHECK (status IN ('todo', 'doing', 'review', 'done', 'returned'));
