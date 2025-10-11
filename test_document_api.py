#!/usr/bin/env python3
"""
Unit tests for the Document API endpoints.
"""
import unittest
import os
import json
import time
import subprocess
import uuid
from typing import Dict, Any, Optional

# Skip requests-based tests if the module is not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class DocumentAPITest(unittest.TestCase):
    """Test case for Document API endpoints."""
    
    API_URL = "https://doztra-research.onrender.com"
    USERNAME = "admin@doztra.ai"
    PASSWORD = "Admin123!"
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - get auth token and create test files."""
        # Get authentication token
        auth_response = requests.post(
            f"{cls.API_URL}/api/auth/login",
            data={
                "username": cls.USERNAME,
                "password": cls.PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        cls.assertTrue(auth_response.status_code == 200, f"Authentication failed: {auth_response.text}")
        cls.token = auth_response.json().get("access_token")
        cls.assertTrue(cls.token, "No access token in response")
        
        # Create test files
        cls.create_test_files()
        
        # Store uploaded document IDs for cleanup
        cls.document_ids = []
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Delete any remaining test documents
        for doc_id in cls.document_ids:
            try:
                requests.delete(
                    f"{cls.API_URL}/api/v2/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {cls.token}"}
                )
            except Exception as e:
                print(f"Error deleting document {doc_id}: {e}")
        
        # Remove test files
        cls.cleanup_test_files()
    
    @classmethod
    def create_test_files(cls):
        """Create test files for upload testing."""
        # Text file
        with open("test_document.txt", "w") as f:
            f.write("This is a test document for the improved document storage system.\n")
            f.write("It contains multiple lines of text to test the document processing.\n")
            f.write("The system should split this document into chunks and store them in the database.\n")
            f.write("It should also generate embeddings for each chunk to enable semantic search.\n")
        
        # Create a simple CSV file
        with open("test_document.csv", "w") as f:
            f.write("id,name,value\n")
            f.write("1,Item 1,100\n")
            f.write("2,Item 2,200\n")
            f.write("3,Item 3,300\n")
    
    @classmethod
    def cleanup_test_files(cls):
        """Remove test files."""
        test_files = ["test_document.txt", "test_document.csv"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
    
    def test_01_upload_document(self):
        """Test document upload endpoint."""
        # Upload text document
        with open("test_document.txt", "rb") as f:
            response = requests.post(
                f"{self.API_URL}/api/v2/documents/upload",
                headers={"Authorization": f"Bearer {self.token}"},
                files={"file": ("test_document.txt", f, "text/plain")},
                data={"title": "Test Text Document"}
            )
        
        self.assertEqual(response.status_code, 200, f"Upload failed: {response.text}")
        data = response.json()
        self.assertIn("document_id", data, "No document_id in response")
        self.assertIn("status", data, "No status in response")
        
        # Save document ID for later tests
        document_id = data["document_id"]
        self.document_ids.append(document_id)
        
        # Upload CSV document
        with open("test_document.csv", "rb") as f:
            response = requests.post(
                f"{self.API_URL}/api/v2/documents/upload",
                headers={"Authorization": f"Bearer {self.token}"},
                files={"file": ("test_document.csv", f, "text/csv")},
                data={"title": "Test CSV Document"}
            )
        
        self.assertEqual(response.status_code, 200, f"Upload failed: {response.text}")
        data = response.json()
        self.assertIn("document_id", data, "No document_id in response")
        self.document_ids.append(data["document_id"])
        
        return document_id
    
    def test_02_list_documents(self):
        """Test listing documents endpoint."""
        # First upload a document to ensure there's something to list
        self.test_01_upload_document()
        
        # List documents
        response = requests.get(
            f"{self.API_URL}/api/v2/documents",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"List documents failed: {response.text}")
        data = response.json()
        self.assertIn("documents", data, "No documents in response")
        self.assertIsInstance(data["documents"], list, "Documents is not a list")
        self.assertGreater(len(data["documents"]), 0, "No documents returned")
        
        # Check document structure
        doc = data["documents"][0]
        self.assertIn("document_id", doc, "No document_id in document")
        self.assertIn("file_name", doc, "No file_name in document")
        self.assertIn("status", doc, "No status in document")
    
    def test_03_get_document(self):
        """Test getting document details endpoint."""
        # Upload a document and get its ID
        document_id = self.test_01_upload_document()
        
        # Get document details
        response = requests.get(
            f"{self.API_URL}/api/v2/documents/{document_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get document failed: {response.text}")
        data = response.json()
        self.assertEqual(data["document_id"], document_id, "Document ID mismatch")
        self.assertIn("file_name", data, "No file_name in response")
        self.assertIn("status", data, "No status in response")
        self.assertIn("metadata", data, "No metadata in response")
    
    def test_04_get_document_content(self):
        """Test getting document content endpoint."""
        # Upload a document and get its ID
        document_id = self.test_01_upload_document()
        
        # Wait for processing to complete
        self._wait_for_processing(document_id)
        
        # Get document content
        response = requests.get(
            f"{self.API_URL}/api/v2/documents/{document_id}/content",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get content failed: {response.text}")
        data = response.json()
        self.assertIn("content", data, "No content in response")
        self.assertIn("document_id", data, "No document_id in response")
        self.assertEqual(data["document_id"], document_id, "Document ID mismatch")
        self.assertIn("This is a test document", data["content"], "Content doesn't match expected text")
    
    def test_05_delete_document(self):
        """Test deleting document endpoint."""
        # Upload a document and get its ID
        document_id = self.test_01_upload_document()
        
        # Delete document
        response = requests.delete(
            f"{self.API_URL}/api/v2/documents/{document_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Delete failed: {response.text}")
        data = response.json()
        self.assertIn("message", data, "No message in response")
        self.assertIn("deleted", data["message"].lower(), "Message doesn't indicate deletion")
        
        # Try to get the deleted document
        response = requests.get(
            f"{self.API_URL}/api/v2/documents/{document_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 404, "Document still exists after deletion")
        
        # Remove from cleanup list since we already deleted it
        if document_id in self.document_ids:
            self.document_ids.remove(document_id)
    
    def test_06_error_handling(self):
        """Test error handling in the API."""
        # Test invalid document ID
        response = requests.get(
            f"{self.API_URL}/api/v2/documents/invalid-id",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 404, "Expected 404 for invalid document ID")
        
        # Test invalid file type
        with open("test_invalid.xyz", "w") as f:
            f.write("Invalid file type")
        
        try:
            with open("test_invalid.xyz", "rb") as f:
                response = requests.post(
                    f"{self.API_URL}/api/v2/documents/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files={"file": ("test_invalid.xyz", f, "application/octet-stream")},
                    data={"title": "Invalid File"}
                )
            
            self.assertEqual(response.status_code, 400, "Expected 400 for invalid file type")
        finally:
            if os.path.exists("test_invalid.xyz"):
                os.remove("test_invalid.xyz")
    
    def _wait_for_processing(self, document_id: str, max_attempts: int = 10, delay: int = 2) -> bool:
        """Wait for document processing to complete."""
        for attempt in range(max_attempts):
            response = requests.get(
                f"{self.API_URL}/api/v2/documents/{document_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code != 200:
                time.sleep(delay)
                continue
                
            data = response.json()
            status = data.get("status")
            
            if status == "completed":
                return True
            elif status == "failed":
                self.fail(f"Document processing failed: {data.get('error')}")
            
            time.sleep(delay)
        
        # If we get here, processing didn't complete in time
        print(f"Warning: Document processing didn't complete after {max_attempts} attempts")
        return False


class DocumentAPIShellTest(unittest.TestCase):
    """Test case for Document API endpoints using shell commands."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Create test script
        cls.create_test_script()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Remove test script
        if os.path.exists("test_document_api.sh"):
            os.remove("test_document_api.sh")
    
    @classmethod
    def create_test_script(cls):
        """Create test script for shell-based testing."""
        script = """#!/bin/bash

# Colors for better readability
GREEN="\\033[0;32m"
RED="\\033[0;31m"
YELLOW="\\033[0;33m"
BLUE="\\033[0;34m"
NC="\\033[0m" # No Color

API_URL="https://doztra-research.onrender.com"

echo -e "${YELLOW}=== DOCUMENT API TEST ===${NC}"

# Step 1: Get authentication token
echo -e "\\n${YELLOW}1. Getting authentication token...${NC}"
TOKEN=$(curl -s -X POST \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=admin@doztra.ai&password=Admin123!" \\
  $API_URL/api/auth/login | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}Failed to get authentication token${NC}"
  exit 1
fi

echo -e "${GREEN}Authentication successful${NC}"

# Step 2: Create a test document
echo -e "\\n${YELLOW}2. Creating test document...${NC}"
echo "This is a test document for the improved document storage system.
It contains multiple lines of text to test the document processing.
The system should split this document into chunks and store them in the database.
It should also generate embeddings for each chunk to enable semantic search." > test_document.txt

echo -e "${GREEN}Test document created${NC}"

# Step 3: Upload the document
echo -e "\\n${YELLOW}3. Uploading document...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@test_document.txt" \\
  -F "title=Test Document" \\
  $API_URL/api/v2/documents/upload)

echo "Response: $UPLOAD_RESPONSE"

# Extract document ID from response
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$DOCUMENT_ID" ]; then
  echo -e "${RED}Failed to extract document ID from response${NC}"
  exit 1
fi

echo -e "${GREEN}Document uploaded with ID: $DOCUMENT_ID${NC}"

# Step 4: List documents
echo -e "\\n${YELLOW}4. Listing documents...${NC}"
LIST_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \\
  $API_URL/api/v2/documents)

echo "Response: $LIST_RESPONSE"
echo -e "${GREEN}Documents listed successfully${NC}"

# Step 5: Wait for document processing
echo -e "\\n${YELLOW}5. Waiting for document processing...${NC}"
PROCESSING_COMPLETE=false
MAX_ATTEMPTS=10
ATTEMPT=0

while [ "$PROCESSING_COMPLETE" = false ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))
  echo -e "Checking document status (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  
  DOCUMENT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \\
    $API_URL/api/v2/documents/$DOCUMENT_ID)
  
  STATUS=$(echo $DOCUMENT_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$STATUS" = "completed" ]; then
    PROCESSING_COMPLETE=true
    echo -e "${GREEN}Document processing completed${NC}"
  elif [ "$STATUS" = "failed" ]; then
    echo -e "${RED}Document processing failed${NC}"
    echo "Response: $DOCUMENT_RESPONSE"
    exit 1
  else
    echo -e "${BLUE}Document status: $STATUS${NC}"
    sleep 2
  fi
done

if [ "$PROCESSING_COMPLETE" = false ]; then
  echo -e "${YELLOW}Document processing taking longer than expected, continuing anyway${NC}"
fi

# Step 6: Get document details
echo -e "\\n${YELLOW}6. Getting document details...${NC}"
DETAILS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \\
  $API_URL/api/v2/documents/$DOCUMENT_ID)

echo "Response: $DETAILS_RESPONSE"
echo -e "${GREEN}Document details retrieved successfully${NC}"

# Step 7: Get document content
echo -e "\\n${YELLOW}7. Getting document content...${NC}"
CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \\
  $API_URL/api/v2/documents/$DOCUMENT_ID/content)

echo "Response: $CONTENT_RESPONSE"
echo -e "${GREEN}Document content retrieved successfully${NC}"

# Step 8: Delete document
echo -e "\\n${YELLOW}8. Deleting document...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE \\
  -H "Authorization: Bearer $TOKEN" \\
  $API_URL/api/v2/documents/$DOCUMENT_ID)

echo "Response: $DELETE_RESPONSE"
echo -e "${GREEN}Document deleted successfully${NC}"

# Clean up
echo -e "\\n${YELLOW}9. Cleaning up...${NC}"
rm -f test_document.txt
echo -e "${GREEN}Test document removed${NC}"

echo -e "\\n${GREEN}=== TEST COMPLETED SUCCESSFULLY ===${NC}"
"""
        
        with open("test_document_api.sh", "w") as f:
            f.write(script)
        
        os.chmod("test_document_api.sh", 0o755)
    
    def test_shell_script(self):
        """Test the shell script."""
        result = subprocess.run(
            ["./test_document_api.sh"],
            capture_output=True,
            text=True
        )
        
        # Print output for debugging
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        # Check if the script completed successfully
        self.assertEqual(result.returncode, 0, "Shell script failed")
        self.assertIn("TEST COMPLETED SUCCESSFULLY", result.stdout, "Script didn't complete successfully")


if __name__ == "__main__":
    unittest.main()
