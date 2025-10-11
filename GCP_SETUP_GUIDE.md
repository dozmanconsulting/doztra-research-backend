# Google Cloud Platform (GCP) Setup Guide

This guide will help you set up Google Cloud Storage for document storage in the Doztra backend service.

## Prerequisites

1. A Google Cloud Platform account
2. Basic familiarity with GCP Console
3. The `gcloud` CLI tool installed (optional but recommended)

## Step 1: Create a GCS Bucket

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Storage > Buckets**
3. Click **CREATE BUCKET**
4. Enter a unique bucket name (e.g., `doztra-documents`)
5. Choose your preferred location type and region
6. Set the default storage class (Standard is recommended)
7. Choose access control (Uniform is recommended)
8. Click **CREATE**

## Step 2: Create a Service Account

1. Navigate to **IAM & Admin > Service Accounts**
2. Click **CREATE SERVICE ACCOUNT**
3. Enter a service account name (e.g., `doztra-document-service`)
4. Add a description (optional)
5. Click **CREATE AND CONTINUE**
6. Assign the following roles:
   - **Storage Object Admin** (roles/storage.objectAdmin)
   - **Storage Admin** (roles/storage.admin)
7. Click **CONTINUE** and then **DONE**

## Step 3: Create and Download a Service Account Key

1. Find your newly created service account in the list
2. Click the three dots menu (⋮) and select **Manage keys**
3. Click **ADD KEY > Create new key**
4. Select **JSON** as the key type
5. Click **CREATE**
6. The key file will be automatically downloaded to your computer
7. Store this file securely - it provides access to your GCP resources

## Step 4: Configure the Doztra Backend

1. Copy the downloaded service account key file to a secure location on your server
2. Update your `.env` file with the following settings:
   ```
   USE_GCS_STORAGE=true
   USE_S3_STORAGE=false
   GCS_BUCKET_NAME=your-bucket-name
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```
3. Run the deployment script:
   ```bash
   ./deploy_document_storage_improvements.sh
   ```
4. When prompted, select `gcs` as the storage backend
5. Enter your bucket name and the path to your service account key file

## Step 5: Verify the Setup

1. Upload a test document using the API
2. Check the GCS bucket to verify that the document was uploaded
3. Check the document status in the API to verify that it was processed correctly

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure your service account has the correct permissions
2. **Invalid Credentials**: Check that the path to your service account key file is correct
3. **Bucket Not Found**: Verify that the bucket name is correct and that it exists

### Checking Logs

If you encounter issues, check the application logs:
```bash
tail -f app.log
```

### Testing GCS Access

You can test GCS access using the `gsutil` command:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
gsutil ls gs://your-bucket-name
```

## Security Considerations

1. **Service Account Key**: Keep your service account key secure and never commit it to version control
2. **Bucket Permissions**: Restrict access to your bucket to only the necessary service accounts
3. **Encryption**: Consider enabling encryption for sensitive documents

## Cost Considerations

1. **Storage Costs**: GCS charges for storage used and data transfer
2. **Operation Costs**: GCS charges for operations like GET, PUT, and LIST
3. **Consider Object Lifecycle**: Set up lifecycle rules to delete or archive old documents

For more information, refer to the [Google Cloud Storage documentation](https://cloud.google.com/storage/docs).
