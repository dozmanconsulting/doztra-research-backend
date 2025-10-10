# CORS Fix for Doztra Backend Service

This document explains the CORS (Cross-Origin Resource Sharing) fix implemented for the Doztra backend service.

## Problem Description

The Doztra frontend application was encountering CORS errors when making requests to the backend service, specifically:

```
Access to fetch at 'https://doztra-ai.netlify.app/documents/query' from origin 'https://doztra.ai' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

This error occurred because:

1. The preflight OPTIONS request was not being handled correctly
2. The necessary CORS headers were not being properly set in the response
3. Not all required origins were included in the allowed origins list

## Changes Made

### 1. Updated CustomCORSMiddleware

The `CustomCORSMiddleware` class in `app/middleware/cors.py` has been updated to:

- Properly handle OPTIONS preflight requests
- Include all necessary CORS headers in the response
- Check if the origin is in the allowed origins list
- Add the `Vary: Origin` header to ensure proper caching behavior

### 2. Updated CORS Configuration in main.py

The CORS middleware configuration in `app/main.py` has been updated to:

- Include all necessary origins
- Specify the allowed headers explicitly
- Set appropriate max age for CORS preflight responses

### 3. Updated Allowed Origins in config.py

The `CORS_ORIGINS` list in `app/core/config.py` has been expanded to include:

- All variations of the doztra.ai domain
- All variations of the doztra-ai.netlify.app domain
- Additional local development servers

### 4. Added Test Script

A test script (`test_cors.sh`) has been created to verify the CORS configuration by:

- Testing OPTIONS preflight requests with different origins
- Testing actual POST requests with different origins

## Deployment Instructions

To deploy this fix:

1. Make sure all the changes are committed to the repository
2. Deploy the updated code to your hosting environment (e.g., Render)

```bash
# If using Git for deployment
git push origin main

# If deploying manually to Render
# Follow the Render deployment process with these updated files
```

3. After deployment, run the test script to verify the fix:

```bash
chmod +x test_cors.sh
./test_cors.sh
```

4. Check the browser console in the frontend application to ensure no CORS errors appear

## Expected Results

After deploying these changes:

1. The preflight OPTIONS requests should receive a 200 response with appropriate CORS headers
2. The actual POST requests should succeed without CORS errors
3. The frontend application should be able to make requests to the backend service without CORS issues

## Additional Notes

- The fix maintains backward compatibility with existing clients
- The CORS configuration is now more permissive while still maintaining security
- If new domains are added in the future, they should be added to the `CORS_ORIGINS` list in `app/core/config.py`
