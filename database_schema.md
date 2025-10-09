# Doztra Auth Service - Database Schema

This document provides a detailed technical description of the database schema for the Doztra Auth Service.

## Tables and Relationships

### User Table

The `users` table stores information about registered users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | Unique identifier (UUID) |
| email | VARCHAR(255) | NOT NULL, UNIQUE | User's email address |
| name | VARCHAR(255) | NOT NULL | User's full name |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'USER' | User role (USER, ADMIN) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether the user account is active |
| is_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether the email is verified |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the user was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the user was last updated |
| last_login | TIMESTAMP | NULL | When the user last logged in |

### Subscription Table

The `subscriptions` table stores information about user subscriptions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | Unique identifier (UUID) |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | References users.id |
| plan | ENUM | NOT NULL | Subscription plan: FREE, BASIC, PROFESSIONAL |
| status | ENUM | NOT NULL | Subscription status: ACTIVE, CANCELED, EXPIRED, PENDING |
| start_date | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the subscription started |
| expires_at | TIMESTAMP | NULL | When the subscription expires (NULL for never) |
| auto_renew | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether the subscription auto-renews |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the record was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the record was last updated |

### RefreshToken Table

The `refresh_tokens` table stores refresh tokens for authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | Unique identifier (UUID) |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | References users.id |
| token | VARCHAR(255) | NOT NULL, UNIQUE | The refresh token string |
| expires_at | TIMESTAMP | NOT NULL | When the token expires |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the token was created |

### ResearchProject Table

The `research_projects` table stores information about user research projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | Unique identifier (UUID) |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | References users.id |
| title | VARCHAR(255) | NOT NULL | Project title |
| description | TEXT | NULL | Project description |
| type | VARCHAR(100) | NOT NULL | Project type (e.g., dissertation, thesis) |
| status | ENUM | NOT NULL, DEFAULT 'active' | Project status: active, archived, completed |
| project_metadata | JSON | NULL | Additional project metadata (academic_level, target_audience, etc.) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the project was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the project was last updated |

### GeneratedContent Table

The `generated_content` table stores AI-generated content for research projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | Unique identifier (UUID) |
| project_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | References research_projects.id |
| section_title | VARCHAR(255) | NOT NULL | Title of the content section |
| content | TEXT | NOT NULL | The generated content text |
| version | INTEGER | NOT NULL, DEFAULT 1 | Content version number |
| content_metadata | JSON | NULL | Metadata about the content generation |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the content was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the content was last updated |

### ContentFeedback Table

The `content_feedback` table stores user feedback on generated content.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | Unique identifier (UUID) |
| content_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | References generated_content.id |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | References users.id |
| rating | INTEGER | NOT NULL | User rating (1-5 scale) |
| comments | TEXT | NULL | User comments on the content |
| feedback_metadata | JSON | NULL | Additional feedback metadata |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the feedback was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the feedback was last updated |

## SQL Schema Creation

```sql
-- Create enum types
CREATE TYPE subscription_plan AS ENUM ('FREE', 'BASIC', 'PROFESSIONAL');
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'CANCELED', 'EXPIRED', 'PENDING');
CREATE TYPE project_status AS ENUM ('active', 'archived', 'completed');

-- Create users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'USER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP NULL
);

-- Create subscriptions table
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan subscription_plan NOT NULL DEFAULT 'FREE',
    status subscription_status NOT NULL DEFAULT 'ACTIVE',
    start_date TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_subscription UNIQUE (user_id)
);

-- Create refresh_tokens table
CREATE TABLE refresh_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create research_projects table
CREATE TABLE research_projects (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    type VARCHAR(100) NOT NULL,
    status project_status NOT NULL DEFAULT 'active',
    project_metadata JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create generated_content table
CREATE TABLE generated_content (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content_metadata JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES research_projects(id) ON DELETE CASCADE
);

-- Create content_feedback table
CREATE TABLE content_feedback (
    id VARCHAR(36) PRIMARY KEY,
    content_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments TEXT NULL,
    feedback_metadata JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_content FOREIGN KEY (content_id) REFERENCES generated_content(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_research_projects_user_id ON research_projects(user_id);
CREATE INDEX idx_generated_content_project_id ON generated_content(project_id);
CREATE INDEX idx_generated_content_section_title ON generated_content(section_title);
CREATE INDEX idx_content_feedback_content_id ON content_feedback(content_id);
CREATE INDEX idx_content_feedback_user_id ON content_feedback(user_id);
```

## Database Migrations

Database migrations are handled using Alembic, which is integrated with SQLAlchemy. The migration scripts are stored in the `alembic/versions` directory.

To generate a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:

```bash
alembic upgrade head
```

## Backup and Recovery

Regular backups of the database should be performed using PostgreSQL's built-in backup tools:

```bash
pg_dump -U postgres -d doztra_auth > doztra_auth_backup_$(date +%Y%m%d).sql
```

To restore from a backup:

```bash
psql -U postgres -d doztra_auth < doztra_auth_backup_20251004.sql
```
