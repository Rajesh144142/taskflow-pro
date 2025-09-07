-- Task Management Dashboard Database Schema
-- Run this script to initialize the database

-- Create database (run this separately if needed)
-- CREATE DATABASE task_dashboard;

-- Connect to the database
-- \c task_dashboard;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create meetings table
CREATE TABLE IF NOT EXISTS meetings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    meeting_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 60 CHECK (duration_minutes > 0),
    location VARCHAR(255),
    meeting_url VARCHAR(500), -- For virtual meetings
    reminder_minutes INTEGER DEFAULT 15 CHECK (reminder_minutes >= 0),
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    meeting_type VARCHAR(50) DEFAULT 'in_person' CHECK (meeting_type IN ('in_person', 'virtual', 'hybrid')),
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled'))
);

-- Create meeting participants table for multiple attendees
CREATE TABLE IF NOT EXISTS meeting_participants (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'attendee' CHECK (role IN ('organizer', 'attendee', 'optional')),
    response_status VARCHAR(50) DEFAULT 'pending' CHECK (response_status IN ('pending', 'accepted', 'declined', 'tentative')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(meeting_id, user_id)
);

-- Create meeting reminders log table
CREATE TABLE IF NOT EXISTS meeting_reminders (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reminder_type VARCHAR(50) DEFAULT 'email' CHECK (reminder_type IN ('email', 'sms', 'push')),
    status VARCHAR(50) DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'pending'))
);

-- Create indexes for meetings
CREATE INDEX IF NOT EXISTS idx_meetings_created_by ON meetings(created_by);
CREATE INDEX IF NOT EXISTS idx_meetings_meeting_date ON meetings(meeting_date);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_active ON meetings(is_active);

-- Create indexes for meeting participants
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_user_id ON meeting_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_response_status ON meeting_participants(response_status);

-- Create indexes for meeting reminders
CREATE INDEX IF NOT EXISTS idx_meeting_reminders_meeting_id ON meeting_reminders(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_reminders_user_id ON meeting_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_reminders_sent_at ON meeting_reminders(reminder_sent_at);

-- Create triggers for meetings
CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
INSERT INTO users (username, email, hashed_password) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QYzK2'), -- password: admin123
('user1', 'user1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QYzK2'), -- password: admin123
('user2', 'user2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QYzK2') -- password: admin123
ON CONFLICT (email) DO NOTHING;

-- Insert sample tasks
INSERT INTO tasks (user_id, title, description, status, priority) 
SELECT 
    u.id,
    'Sample Task ' || u.username,
    'This is a sample task for ' || u.username,
    CASE 
        WHEN u.username = 'admin' THEN 'completed'
        WHEN u.username = 'user1' THEN 'in_progress'
        ELSE 'pending'
    END,
    CASE 
        WHEN u.username = 'admin' THEN 'high'
        WHEN u.username = 'user1' THEN 'medium'
        ELSE 'low'
    END
FROM users u
ON CONFLICT DO NOTHING;

-- Display created tables
SELECT 'Database initialized successfully!' as message;
SELECT 'Users table:' as info;
SELECT COUNT(*) as user_count FROM users;
SELECT 'Tasks table:' as info;
SELECT COUNT(*) as task_count FROM tasks;
SELECT 'Meetings table:' as info;
SELECT COUNT(*) as meeting_count FROM meetings;
SELECT 'Meeting participants table:' as info;
SELECT COUNT(*) as participant_count FROM meeting_participants;
SELECT 'Meeting reminders table:' as info;
SELECT COUNT(*) as reminder_count FROM meeting_reminders;
