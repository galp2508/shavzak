-- Add is_ai_generated column to assignments table
-- This column tracks whether an assignment was created by the AI/ML system

ALTER TABLE assignments ADD COLUMN IF NOT EXISTS is_ai_generated BOOLEAN DEFAULT FALSE;

-- Update existing assignments created by the "שיבוץ אוטומטי" shavzak to be marked as AI-generated
UPDATE assignments
SET is_ai_generated = TRUE
WHERE shavzak_id IN (
    SELECT id FROM shavzakim WHERE name = 'שיבוץ אוטומטי'
);
