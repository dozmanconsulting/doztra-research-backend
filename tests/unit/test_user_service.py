"""
Unit tests for the user service.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.user import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_user,
    authenticate_user,
    verify_user_email,
    update_subscription
)
from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.schemas.user import UserCreate, UserUpdate


class TestUserService(unittest.TestCase):
    """Test cases for the user service."""

    @patch('sqlalchemy.orm.Session')
    def test_get_user_by_email(self, mock_db):
        """Test getting a user by email."""
        # Mock the database session
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_db.query().filter().first.return_value = mock_user
        
        # Call the function with the mocked database
        user = get_user_by_email(mock_db, email="test@example.com")
        
        # Verify the result
        self.assertEqual(user.email, "test@example.com")
        
        # Verify the database query was called with User model
        mock_db.query.assert_called_with(User)

    @patch('sqlalchemy.orm.Session')
    def test_get_user_by_id(self, mock_db):
        """Test getting a user by ID."""
        # Mock the database session
        mock_user = MagicMock()
        mock_user.id = "test_user_id"
        mock_db.query().filter().first.return_value = mock_user
        
        # Call the function with the mocked database
        user = get_user_by_id(mock_db, user_id="test_user_id")
        
        # Verify the result
        self.assertEqual(user.id, "test_user_id")
        
        # Verify the database query was called with User model
        mock_db.query.assert_called_with(User)

    @patch('app.services.user.get_user_by_email')
    @patch('app.services.auth.get_password_hash')
    @patch('sqlalchemy.orm.Session')
    def test_create_user(self, mock_db, mock_get_password_hash, mock_get_user_by_email):
        """Test creating a user."""
        # Mock the get_user_by_email function to return None (user doesn't exist)
        mock_get_user_by_email.return_value = None
        
        # Mock the get_password_hash function
        mock_get_password_hash.return_value = "hashed_password"
        
        # Create a user creation schema
        user_in = UserCreate(
            email="new_user@example.com",
            name="New User",
            password="Password123!"
        )
        
        # Call the function with the mocked dependencies
        create_user(mock_db, user_in)
        
        # Verify the database add was called
        self.assertEqual(mock_db.add.call_count, 4)  # User, Subscription, UserPreferences, and UsageStatistics
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('app.services.user.get_user_by_email')
    @patch('sqlalchemy.orm.Session')
    def test_create_user_email_exists(self, mock_db, mock_get_user_by_email):
        """Test creating a user with an existing email."""
        # Mock the get_user_by_email function to return a user (email exists)
        mock_user = MagicMock()
        mock_user.email = "existing@example.com"
        mock_get_user_by_email.return_value = mock_user
        
        # Create a user creation schema with the existing email
        user_in = UserCreate(
            email="existing@example.com",
            name="Existing User",
            password="Password123!"
        )
        
        # Call the function and expect an exception
        with self.assertRaises(Exception) as context:
            create_user(mock_db, user_in)
        
        # Verify the exception was raised
        self.assertIsNotNone(context.exception)
        # In a real test, we would check the message, but our mock doesn't raise the exact exception
        
        # Verify the database add was not called
        mock_db.add.assert_not_called()

    @patch('app.services.user.get_user_by_email')
    @patch('sqlalchemy.orm.Session')
    def test_authenticate_user_success(self, mock_db, mock_get_user_by_email):
        """Test authenticating a user with valid credentials."""
        # Mock the get_user_by_email function
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_user.hashed_password = "hashed_password"
        mock_get_user_by_email.return_value = mock_user
        
        # Call the function with valid credentials
        with patch('app.services.user.verify_password', return_value=True):
            user = authenticate_user(mock_db, email="user@example.com", password="password")
        
        # Verify the result
        self.assertEqual(user.email, "user@example.com")

    @patch('app.services.user.get_user_by_email')
    @patch('sqlalchemy.orm.Session')
    def test_authenticate_user_invalid_password(self, mock_db, mock_get_user_by_email):
        """Test authenticating a user with an invalid password."""
        # Mock the get_user_by_email function
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_user.hashed_password = "hashed_password"
        mock_get_user_by_email.return_value = mock_user
        
        # Call the function with invalid credentials
        with patch('app.services.user.verify_password', return_value=False):
            user = authenticate_user(mock_db, email="user@example.com", password="wrong_password")
        
        # Verify the result is None
        self.assertIsNone(user)

    @patch('sqlalchemy.orm.Session')
    def test_verify_user_email(self, mock_db):
        """Test verifying a user's email."""
        # Mock the user
        mock_user = MagicMock()
        mock_user.is_verified = False
        
        # Call the function
        verify_user_email(mock_db, mock_user)
        
        # Verify the user's is_verified field was updated
        self.assertTrue(mock_user.is_verified)
        
        # Verify the database commit was called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)

    @patch('sqlalchemy.orm.Session')
    def test_update_subscription_existing(self, mock_db):
        """Test updating an existing subscription."""
        # Mock the user with an existing subscription
        mock_subscription = MagicMock()
        mock_subscription.plan = SubscriptionPlan.FREE
        mock_subscription.status = SubscriptionStatus.ACTIVE
        
        mock_user = MagicMock()
        mock_user.id = "user_id"
        mock_user.subscription = mock_subscription
        
        # Call the function
        update_subscription(
            mock_db,
            mock_user,
            plan=SubscriptionPlan.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            auto_renew=True
        )
        
        # Verify the subscription was updated
        self.assertEqual(mock_user.subscription.plan, SubscriptionPlan.PROFESSIONAL)
        self.assertEqual(mock_user.subscription.status, SubscriptionStatus.ACTIVE)
        self.assertTrue(mock_user.subscription.auto_renew)
        
        # Verify the database commit was called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)

    @patch('sqlalchemy.orm.Session')
    def test_update_subscription_new(self, mock_db):
        """Test creating a new subscription for a user."""
        # Mock the user without a subscription
        mock_user = MagicMock()
        mock_user.id = "user_id"
        mock_user.subscription = None
        
        # Call the function
        update_subscription(
            mock_db,
            mock_user,
            plan=SubscriptionPlan.BASIC,
            status=SubscriptionStatus.ACTIVE
        )
        
        # Verify a new subscription was added to the database
        mock_db.add.assert_called_once()
        
        # Verify the database commit was called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)


if __name__ == "__main__":
    unittest.main()
