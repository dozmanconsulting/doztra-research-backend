-- Fix the unique constraint on representatives email and insert default representative

-- Add unique constraint to email column if it doesn't exist
DO $$ 
BEGIN 
    -- Check if unique constraint already exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'representatives' 
        AND constraint_type = 'UNIQUE' 
        AND constraint_name LIKE '%email%'
    ) THEN
        ALTER TABLE representatives ADD CONSTRAINT representatives_email_unique UNIQUE (email);
    END IF;
END $$;

-- Insert default representative (now with proper constraint)
INSERT INTO representatives (name, email, status, is_online) 
VALUES ('System Representative', 'system@doztra.com', 'online', true)
ON CONFLICT (email) DO NOTHING;
