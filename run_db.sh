psql "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"

export DATABASE_URL="postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"

# Connect to the database
psql "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"

# Connect to the database
psql "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"

# List all tables with their sizes
\dt+

# Check the schema of the users table
\d users

# Check the schema of the subscriptions table
\d subscriptions

# Verify admin user exists
SELECT id, email, name, role, is_active, is_verified FROM users WHERE email = 'admin@doztra.ai';

# Check database size and table sizes
SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
SELECT 
    table_name, 
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as total_size
FROM 
    information_schema.tables
WHERE 
    table_schema = 'public'
ORDER BY 
    pg_total_relation_size(quote_ident(table_name)) DESC;

# Check PostgreSQL version
SELECT version();

# Check existing enum types
SELECT 
    t.typname AS enum_name,
    e.enumlabel AS enum_value
FROM 
    pg_type t, 
    pg_enum e
WHERE 
    t.oid = e.enumtypid
ORDER BY 
    t.typname, e.enumsortorder;

# Check database connections
SELECT 
    datname, 
    usename, 
    pid, 
    client_addr, 
    application_name,
    state, 
    query_start
FROM 
    pg_stat_activity
WHERE 
    datname = current_database();

# Check table row counts
SELECT 
    schemaname, 
    relname, 
    n_live_tup
FROM 
    pg_stat_user_tables
ORDER BY 
    n_live_tup DESC;

# Check database indexes
SELECT
    t.relname AS table_name,
    i.relname AS index_name,
    a.attname AS column_name
FROM
    pg_class t,
    pg_class i,
    pg_index ix,
    pg_attribute a
WHERE
    t.oid = ix.indrelid
    AND i.oid = ix.indexrelid
    AND a.attrelid = t.oid
    AND a.attnum = ANY(ix.indkey)
    AND t.relkind = 'r'
    AND t.relname NOT LIKE 'pg_%'
ORDER BY
    t.relname,
    i.relname;