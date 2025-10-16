-- Fix Support Schema - Add missing columns and tables
-- Run this script to resolve the database schema issues

-- First, create the representatives table if it doesn't exist
CREATE TABLE IF NOT EXISTS representatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    status VARCHAR DEFAULT 'offline',
    max_concurrent_chats INTEGER DEFAULT 5,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the support_chats table if it doesn't exist
CREATE TABLE IF NOT EXISTS support_chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    representative_id UUID REFERENCES representatives(id),
    user_email VARCHAR,
    user_name VARCHAR,
    status VARCHAR DEFAULT 'waiting',
    priority VARCHAR DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    user_rating INTEGER
);

-- Create the support_messages table if it doesn't exist
CREATE TABLE IF NOT EXISTS support_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES support_chats(id),
    sender_id UUID,
    sender_type VARCHAR,
    sender_name VARCHAR,
    message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE
);

-- Add missing columns if they don't exist
-- Add last_seen to representatives table
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'representatives' AND column_name = 'last_seen') THEN
        ALTER TABLE representatives ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Add user_email to support_chats table
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'support_chats' AND column_name = 'user_email') THEN
        ALTER TABLE support_chats ADD COLUMN user_email VARCHAR;
    END IF;
END $$;

-- Add user_name to support_chats table
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'support_chats' AND column_name = 'user_name') THEN
        ALTER TABLE support_chats ADD COLUMN user_name VARCHAR;
    END IF;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_representatives_email ON representatives(email);
CREATE INDEX IF NOT EXISTS idx_representatives_is_online ON representatives(is_online);
CREATE INDEX IF NOT EXISTS idx_support_chats_user_id ON support_chats(user_id);
CREATE INDEX IF NOT EXISTS idx_support_chats_representative_id ON support_chats(representative_id);
CREATE INDEX IF NOT EXISTS idx_support_chats_status ON support_chats(status);
CREATE INDEX IF NOT EXISTS idx_support_messages_chat_id ON support_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_support_messages_timestamp ON support_messages(timestamp);

-- Insert a default representative for testing (optional)
INSERT INTO representatives (name, email, status, is_online) 
VALUES ('System Representative', 'system@doztra.com', 'online', true)
ON CONFLICT (email) DO NOTHING;

COMMIT;
