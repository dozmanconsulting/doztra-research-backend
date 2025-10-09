# Doztra Auth Service - Architecture Diagram

This document provides a visual representation of the Doztra Auth Service architecture and how it integrates with other components of the Doztra AI Platform.

## System Architecture

```mermaid
graph TD
    subgraph "Client Applications"
        WebApp["Web App\n(React)"]
        MobileApp["Mobile App\n(React Native)"]
    end

    subgraph "API Gateway"
        Gateway["API Gateway / Load Balancer"]
    end

    subgraph "Doztra Auth Service"
        AuthAPI["Auth API\n(FastAPI)"]
        AuthDB[(PostgreSQL DB)]
        EmailService["Email Service"]
        
        AuthAPI -- "CRUD operations" --> AuthDB
        AuthAPI -- "Send emails" --> EmailService
    end

    subgraph "Other Doztra Services"
        ChatService["Chat Service"]
        PlagiarismService["Plagiarism Checker Service"]
        PromptService["Prompt Generation Service"]
    end

    WebApp -- "HTTP/HTTPS" --> Gateway
    MobileApp -- "HTTP/HTTPS" --> Gateway
    
    Gateway -- "Route auth requests" --> AuthAPI
    Gateway -- "Route chat requests" --> ChatService
    Gateway -- "Route plagiarism requests" --> PlagiarismService
    Gateway -- "Route prompt requests" --> PromptService
    
    ChatService -- "Validate tokens" --> AuthAPI
    PlagiarismService -- "Validate tokens" --> AuthAPI
    PromptService -- "Validate tokens" --> AuthAPI
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Client as Client App
    participant Auth as Auth Service
    participant DB as Database
    participant Email as Email Service
    participant Other as Other Services
    
    %% Registration Flow
    User->>Client: Register with email/password
    Client->>Auth: POST /api/auth/register
    Auth->>DB: Create user record
    Auth->>Email: Send verification email
    Auth-->>Client: Return user data & tokens
    Client-->>User: Show success message
    
    %% Email Verification Flow
    User->>Client: Click verification link in email
    Client->>Auth: POST /api/auth/verify-email/{token}
    Auth->>DB: Update user.is_verified = true
    Auth-->>Client: Return success message
    Client-->>User: Show verification success
    
    %% Login Flow
    User->>Client: Login with email/password
    Client->>Auth: POST /api/auth/login
    Auth->>DB: Validate credentials
    Auth->>DB: Create refresh token
    Auth-->>Client: Return access & refresh tokens
    Client->>Client: Store tokens
    Client-->>User: Redirect to dashboard
    
    %% Using Protected Services
    User->>Client: Request protected resource
    Client->>Other: Request with access token
    Other->>Auth: Validate access token
    Auth-->>Other: Token validation result
    Other-->>Client: Protected resource data
    Client-->>User: Display data
    
    %% Token Refresh
    Client->>Auth: POST /api/auth/refresh
    Auth->>DB: Validate refresh token
    Auth->>DB: Delete old refresh token
    Auth->>DB: Create new refresh token
    Auth-->>Client: New access & refresh tokens
    Client->>Client: Update stored tokens
    
    %% Logout
    User->>Client: Logout
    Client->>Auth: POST /api/auth/logout
    Auth->>DB: Delete refresh token
    Auth-->>Client: Logout success
    Client->>Client: Clear stored tokens
    Client-->>User: Redirect to login page
```

## Component Diagram

```mermaid
classDiagram
    class AuthService {
        +register(user_data)
        +login(email, password)
        +refresh_token(refresh_token)
        +logout(refresh_token)
        +verify_email(token)
        +reset_password(token, new_password)
    }
    
    class UserService {
        +get_user_profile(user_id)
        +update_user_profile(user_id, data)
        +update_subscription(user_id, plan)
    }
    
    class TokenService {
        +create_access_token(user_id)
        +create_refresh_token(user_id)
        +verify_token(token)
    }
    
    class EmailService {
        +send_verification_email(email, token)
        +send_password_reset_email(email, token)
        +send_welcome_email(email, name)
    }
    
    class Database {
        +users
        +subscriptions
        +refresh_tokens
    }
    
    AuthService --> TokenService: uses
    AuthService --> UserService: uses
    AuthService --> EmailService: uses
    UserService --> Database: accesses
    TokenService --> Database: accesses
```

## Deployment Architecture

```mermaid
graph TD
    subgraph "Production Environment"
        LB["Load Balancer"]
        
        subgraph "Kubernetes Cluster"
            AuthPod1["Auth Service Pod 1"]
            AuthPod2["Auth Service Pod 2"]
            AuthPod3["Auth Service Pod 3"]
        end
        
        DBPrimary[(PostgreSQL Primary)]
        DBReplica[(PostgreSQL Replica)]
        
        Redis["Redis Cache"]
        
        subgraph "Monitoring"
            Prometheus["Prometheus"]
            Grafana["Grafana Dashboard"]
        end
    end
    
    LB --> AuthPod1
    LB --> AuthPod2
    LB --> AuthPod3
    
    AuthPod1 --> DBPrimary
    AuthPod2 --> DBPrimary
    AuthPod3 --> DBPrimary
    
    AuthPod1 -.-> DBReplica
    AuthPod2 -.-> DBReplica
    AuthPod3 -.-> DBReplica
    
    AuthPod1 --> Redis
    AuthPod2 --> Redis
    AuthPod3 --> Redis
    
    AuthPod1 -.-> Prometheus
    AuthPod2 -.-> Prometheus
    AuthPod3 -.-> Prometheus
    
    Prometheus --> Grafana
    
    DBPrimary --> DBReplica
```

## Security Measures

1. **Authentication**:
   - JWT tokens with short expiration
   - Refresh tokens with rotation
   - Password hashing using bcrypt

2. **Data Protection**:
   - HTTPS for all communications
   - Database encryption at rest
   - Sensitive data masking in logs

3. **Access Control**:
   - Role-based access control
   - Token validation for all protected endpoints
   - Rate limiting to prevent abuse

4. **Monitoring**:
   - Real-time security alerts
   - Failed authentication attempt monitoring
   - Regular security audits
