# Frontend Fix Recommendation

## Issue: Invalid Project ID Format

The backend is now correctly validating project IDs and returning a 400 Bad Request when an invalid format is provided. However, the frontend is still sending project IDs in an invalid format (e.g., "project-1" instead of a valid UUID).

## Solution

Update the frontend code to ensure it's sending valid UUIDs for project IDs. Here's what needs to be fixed:

1. **Locate the component that makes the content generation request**:
   - Look for code that calls the `/api/research/content/generate-section` endpoint
   - This is likely in a component related to research projects or content generation

2. **Update the request payload**:
   - Ensure the `project_id` field contains a valid UUID from the database
   - Replace any hardcoded values like "project-1" with actual project IDs

3. **Example fix**:

```javascript
// Before
const generateContent = async () => {
  const response = await api.post('/api/research/content/generate-section', {
    project_id: 'project-1', // Invalid format
    section_title: 'Introduction'
  });
  // ...
};

// After
const generateContent = async (projectId) => {
  const response = await api.post('/api/research/content/generate-section', {
    project_id: projectId, // Use the actual UUID from the database
    section_title: 'Introduction'
  });
  // ...
};
```

4. **Update any UI components**:
   - Make sure dropdown menus, select boxes, or other UI elements that allow users to select projects are populated with actual project IDs from the database
   - Ensure that when a user selects a project, the actual UUID is used in the request

5. **Add error handling**:
   - Add proper error handling to display a user-friendly message when the backend returns a 400 error
   - Consider adding client-side validation to prevent invalid project IDs from being sent

## Testing

After making these changes, test the content generation feature to ensure:
1. Valid project IDs are being sent to the backend
2. Content is successfully generated
3. Error messages are properly displayed when something goes wrong

## Additional Notes

The backend now has proper validation for project IDs, so any invalid format will be rejected with a clear error message. This should help with debugging and ensure that only valid data is processed.
