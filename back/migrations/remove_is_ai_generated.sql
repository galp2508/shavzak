-- Remove is_ai_generated column from assignments table
-- This column is no longer needed

ALTER TABLE assignments DROP COLUMN IF EXISTS is_ai_generated;
