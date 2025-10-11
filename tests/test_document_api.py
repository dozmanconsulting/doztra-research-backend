import unittest
import os
import sys
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.services.document_service import DocumentService
from app.services.auth_service import create_access_token

class TestDocumentAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Create a test user
        self.test_user_id = str(uuid.uuid4())
        self.access_token = create_access_token({"sub": self.test_user_id})
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Mock document data
        self.test_document_id = str(uuid.uuid4())
        self.test_document = {
            "document_id": self.test_document_id,
            "user_id": self.test_user_id,
            "file_name": "test_document.pdf",
            "file_type": "application/pdf",
            "file_size": 12345,
            "upload_date": "2025-10-11T08:14:05.196397",
            "status": "completed",
            "message": "Document processed successfully"
        }
        
        self.test_document_content = {
            "document_id": self.test_document_id,
            "content": "This is the test document content",
            "chunk_count": 1
        }

    @patch.object(DocumentService, 'get_document')
    def test_get_document(self, mock_get_document):
        # Setup
        mock_get_document.return_value = self.test_document
        
        # Execute
        response = self.client.get(f"/api/v2/documents/{self.test_document_id}", headers=self.headers)
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["document_id"], self.test_document_id)
        self.assertEqual(response.json()["file_name"], "test_document.pdf")
        mock_get_document.assert_called_once_with(self.test_document_id, self.test_user_id)

    @patch.object(DocumentService, 'get_document_content')
    def test_get_document_content(self, mock_get_document_content):
        # Setup
        mock_get_document_content.return_value = self.test_document_content
        
        # Execute
        response = self.client.get(f"/api/v2/documents/{self.test_document_id}/content", headers=self.headers)
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["document_id"], self.test_document_id)
        self.assertEqual(response.json()["content"], "This is the test document content")
        self.assertEqual(response.json()["chunk_count"], 1)
        mock_get_document_content.assert_called_once_with(self.test_document_id, self.test_user_id)

    @patch.object(DocumentService, 'get_document')
    def test_get_document_not_found(self, mock_get_document):
        # Setup
        mock_get_document.return_value = None
        
        # Execute
        response = self.client.get(f"/api/v2/documents/{self.test_document_id}", headers=self.headers)
        
        # Verify
        self.assertEqual(response.status_code, 404)
        self.assertIn("Document not found", response.json()["detail"])

    @patch.object(DocumentService, 'get_document')
    @patch.object(DocumentService, 'get_document_content')
    def test_get_document_content_not_found(self, mock_get_document_content, mock_get_document):
        # Setup
        mock_get_document.return_value = None
        
        # Execute
        response = self.client.get(f"/api/v2/documents/{self.test_document_id}/content", headers=self.headers)
        
        # Verify
        self.assertEqual(response.status_code, 404)
        self.assertIn("Document not found", response.json()["detail"])
        mock_get_document_content.assert_not_called()

    def test_get_document_unauthorized(self):
        # Execute without auth headers
        response = self.client.get(f"/api/v2/documents/{self.test_document_id}")
        
        # Verify
        self.assertEqual(response.status_code, 401)
        self.assertIn("Not authenticated", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
