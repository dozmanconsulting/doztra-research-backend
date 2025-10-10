# Document Processing Troubleshooting

This directory contains scripts to help diagnose and fix document processing issues in the Doztra backend service.

## Issue Description

Users may encounter the following issues with document processing:
- Documents show as "still being processed" even after a long time
- Document queries return no results or errors
- Document content is not available

## Diagnostic Scripts

### 1. Check Document Status

Use this script to check the status of a document:

```bash
./check_document_status.sh <document_id> <access_token>
```

Example:
```bash
./check_document_status.sh doc-9a11651a-4c56-49a7-8d17-4d048326226c eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

This script will:
- Check if the document exists in the API
- Check if document content is available
- Test a simple query on the document

### 2. Document Processing Debug

For more detailed diagnostics, use the Python debug script:

```bash
./document_processing_debug.py --document-id <document_id> --token <access_token> [--api-url <api_url>] [--db-url <db_url>]
```

Example:
```bash
./document_processing_debug.py --document-id doc-9a11651a-4c56-49a7-8d17-4d048326226c --token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... --api-url https://doztra-research.onrender.com --db-url postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng
```

This script will:
- Check document status via API
- Check document content
- Check document in database (if DB URL provided)
- Check document processing queue
- Check document processing logs
- Test document query
- Check document processing code
- Provide recommendations based on findings

## Fix Scripts

### Fix Document Processing

Use this script to fix common document processing issues:

```bash
./fix_document_processing.py [--document-id <document_id>] [--fix-all] [--db-url <db_url>] [--reset-processing] [--clear-queue]
```

Options:
- `--document-id`: Fix a specific document
- `--fix-all`: Fix all stuck documents
- `--db-url`: Database URL (optional)
- `--reset-processing`: Reset processing status for stuck documents
- `--clear-queue`: Clear document processing queue

Example:
```bash
./fix_document_processing.py --document-id doc-9a11651a-4c56-49a7-8d17-4d048326226c --db-url postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng
```

## Common Issues and Solutions

### 1. Document Stuck in Processing

**Symptoms:**
- Document shows as "still being processed"
- Document content is not available

**Solutions:**
- Run `fix_document_processing.py --document-id <document_id> --reset-processing`
- If that doesn't work, try `fix_document_processing.py --document-id <document_id> --clear-queue`
- Restart the application after applying fixes

### 2. Document Query Not Working

**Symptoms:**
- Document exists but queries return errors
- "The document is still being processed" message

**Solutions:**
- Check if document content is available using `check_document_status.sh`
- If content is available but queries fail, there might be an issue with the query service
- Try re-uploading the document if possible

### 3. Database Schema Issues

**Symptoms:**
- Errors about missing columns or tables

**Solutions:**
- Run `fix_document_processing.py --fix-all` to add missing columns
- Check database migrations to ensure they've been applied correctly

## Monitoring

After applying fixes, monitor the application logs for any new issues. You may need to restart the application for some fixes to take effect.
