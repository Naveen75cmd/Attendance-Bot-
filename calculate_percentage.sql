-- 1. Add column to students table
ALTER TABLE students ADD COLUMN IF NOT EXISTS attendance_percentage DECIMAL(5,2);

-- 2. Query to UPDATE the percentage based on current data
-- Formula: (Count of Present+OD+Late) / Total Sessions * 100

WITH stats AS (
    SELECT
        s.id as student_id,
        COUNT(a.id) as total,
        SUM(CASE WHEN a.status IN ('Present', 'OD', 'Late') THEN 1 ELSE 0 END) as present_count
    FROM students s
    LEFT JOIN attendance a ON s.id = a.student_id
    GROUP BY s.id
)
UPDATE students
SET attendance_percentage = CASE 
    WHEN stats.total > 0 THEN (stats.present_count::decimal / stats.total::decimal) * 100 
    ELSE 0 
END
FROM stats
WHERE students.id = stats.student_id;
