-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    register_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    section TEXT NOT NULL CHECK (section IN ('A', 'B')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    session TEXT NOT NULL CHECK (session IN ('Morning', 'Afternoon')),
    status TEXT NOT NULL CHECK (status IN ('Present', 'Absent', 'OD', 'Late')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(student_id, date, session)
);

-- Enable Row Level Security (RLS)
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;

-- Create policies (open for all for this simpler tool, or restrict as needed)
-- For this prototype, we'll allow anon access if the key is provided, but in prod assume authenticated staff
CREATE POLICY "Allow anon read/write access" ON students FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon read/write access" ON attendance FOR ALL USING (true) WITH CHECK (true);
