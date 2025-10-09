# Changelog

All notable changes to the Doztra Auth Service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Token usage tracking and analytics
- User preferences management
- Usage statistics tracking
- Payment integration with Stripe
- Enhanced subscription management with tiered plans
- Model tier access control based on subscription
- Admin analytics dashboard for token usage

## [0.2.0] - 2025-10-04

### Added
- Token usage tracking and analytics
- User preferences management
- Usage statistics tracking
- Payment integration with Stripe
- Enhanced subscription management with tiered plans
- Model tier access control based on subscription
- Admin analytics dashboard for token usage

### Changed
- Updated user registration to include subscription information
- Updated login response to include user profile data
- Enhanced API responses with consistent success field
- Improved error handling for connection issues

### Security
- Added model tier access control based on subscription
- Added token usage limits based on subscription plan

## [0.1.0] - 2025-10-04

### Added
- Initial release
- Core authentication functionality
- User management
- Subscription management
- Email services
- API documentation

### Security
- Password hashing with bcrypt
- JWT token authentication
- Refresh token rotation
- Email verification

## Types of changes
- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for soon-to-be removed features.
- **Removed** for now removed features.
- **Fixed** for any bug fixes.
- **Security** in case of vulnerabilities.
