# Doztra Authentication Service

A FastAPI-based authentication service for the Doztra AI Platform, providing secure user management, authentication, and subscription services.


## Features

- User registration and login with JWT authentication
- Refresh token mechanism for persistent sessions
- Email verification and password reset functionality
- User profile management
- Subscription management with tiered plans
- Token usage tracking and analytics
- User preferences management
- Usage statistics tracking
- Payment integration with Stripe
- Enhanced subscription management with tiered plans
- Model tier access control based on subscription
- Admin analytics dashboard for token usage
- Comprehensive admin panel with user management
- Advanced user filtering and sorting
- User statistics and analytics
- Admin user creation and management

## Tech Stack

- **FastAPI**: Modern, high-performance web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM for database interactions
- **PostgreSQL**: Robust relational database for data storage
- **Pydantic**: Data validation and settings management
- **JWT**: JSON Web Tokens for secure authentication
- **Alembic**: Database migration tool
- **Jinja2**: Template engine for email templates
- **Docker**: Containerization for consistent deployment

## API Endpoints

### Authentication

- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login and get access token
- `POST /api/auth/refresh`: Refresh access token
- `POST /api/auth/logout`: Logout and invalidate refresh token
- `POST /api/auth/verify-email/{token}`: Verify email address
- `POST /api/auth/password-reset`: Request password reset
- `POST /api/auth/reset-password`: Reset password with token

### Users

- `GET /api/users/me`: Get current user profile
- `PUT /api/users/me`: Update current user profile
- `GET /api/users/{user_id}`: Get user by ID
- `PUT /api/users/me/subscription`: Update user subscription
- `GET /api/users/me/subscription`: Get user subscription details
- `GET /api/users/me/usage`: Get user usage statistics

### Token Usage

- `GET /api/tokens/me`: Get user token usage statistics
- `GET /api/tokens/me/history`: Get user token usage history
- `POST /api/tokens/me/track`: Track token usage
- `GET /api/tokens/admin/usage`: Get admin token usage analytics

### User Preferences

- `GET /api/preferences/me`: Get user preferences
- `PUT /api/preferences/me`: Update user preferences

### Usage Statistics

- `GET /api/usage/me`: Get user usage statistics

### Admin

- `GET /api/admin/dashboard`: Get admin dashboard statistics
- `GET /api/admin/users`: Get all users with filtering and sorting
- `GET /api/admin/users/{user_id}`: Get a specific user
- `POST /api/admin/users`: Create a new user
- `PATCH /api/admin/users/{user_id}/status`: Update a user's status
- `DELETE /api/admin/users/{user_id}`: Delete a user
- `GET /api/admin/users/statistics`: Get user statistics

## Project Structure

```
├── alembic/                # Database migration scripts
├── app/
│   ├── api/               # API endpoints
│   │   └── routes/        # Route definitions
│   ├── core/              # Core application code
│   ├── db/                # Database setup and session management
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas for request/response validation
│   ├── services/          # Business logic services
│   ├── static/            # Static files (CSS, JS, images)
│   ├── templates/         # Email templates
│   ├── utils/             # Utility functions
│   └── main.py            # FastAPI application entry point
├── tests/
│   ├── unit/             # Unit tests
│   └── api_tests.py      # API integration tests
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── ADMIN_API.md          # Admin API documentation
├── ADMIN_FEATURES.md     # Admin features documentation
├── alembic.ini           # Alembic configuration
├── CHANGELOG.md          # Changelog
├── database_erd.md       # Entity Relationship Diagram
├── database_schema.md    # Database schema documentation
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── IMPLEMENTATION_SUMMARY.md # Implementation summary
├── init_db.py            # Database initialization script
├── NEW_FEATURES.md       # New features documentation
├── pytest.ini            # Pytest configuration
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
└── run.py                # Application runner script
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please contact support@doztra.ai
