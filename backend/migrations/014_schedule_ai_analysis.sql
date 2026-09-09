-- Persist last AI schedule analysis on the project for reload.
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS schedule_ai_analysis TEXT NULL,
  ADD COLUMN IF NOT EXISTS schedule_generation_mode VARCHAR(40) NULL;
