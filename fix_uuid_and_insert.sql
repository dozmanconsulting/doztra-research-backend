-- Fix UUID generation and insert default representative

-- Enable uuid-ossp extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Update the representatives table to use uuid_generate_v4() instead of gen_random_uuid()
ALTER TABLE representatives ALTER COLUMN id SET DEFAULT uuid_generate_v4();

-- Insert default representative with explicit UUID
INSERT INTO representatives (id, name, email, status, is_online) 
VALUES (uuid_generate_v4(), 'System Representative', 'system@doztra.com', 'online', true)
ON CONFLICT (email) DO NOTHING;
