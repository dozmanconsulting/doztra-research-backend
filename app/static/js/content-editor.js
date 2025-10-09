/**
 * Content Editor functionality for saving changes to generated content
 */

class ContentEditor {
  constructor(options = {}) {
    this.apiBaseUrl = options.apiBaseUrl || '/api/research';
    this.token = options.token || '';
    this.projectId = options.projectId || '';
    this.sectionTitle = options.sectionTitle || '';
    this.content = options.content || '';
    this.onSaveSuccess = options.onSaveSuccess || (() => {});
    this.onSaveError = options.onSaveError || (() => {});
  }

  /**
   * Initialize the editor
   */
  init(editorElement) {
    this.editorElement = editorElement;
    
    // Add event listeners for save button
    const saveButton = document.getElementById('save-changes-btn');
    if (saveButton) {
      saveButton.addEventListener('click', () => this.saveChanges());
    }
  }

  /**
   * Get the current content from the editor
   */
  getCurrentContent() {
    return this.editorElement.value || this.editorElement.innerHTML;
  }

  /**
   * Save changes to the backend
   */
  async saveChanges() {
    try {
      const updatedContent = this.getCurrentContent();
      
      // Show saving indicator
      this.showSavingIndicator();
      
      const response = await fetch(`${this.apiBaseUrl}/projects/${this.projectId}/content/section/${encodeURIComponent(this.sectionTitle)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`
        },
        body: JSON.stringify({
          content: updatedContent,
          content_metadata: {
            last_edited_client_timestamp: new Date().toISOString()
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save changes: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Update local content
      this.content = data.content;
      
      // Show success message
      this.showSuccessMessage();
      
      // Call success callback
      this.onSaveSuccess(data);
      
      return data;
    } catch (error) {
      console.error('Error saving changes:', error);
      
      // Show error message
      this.showErrorMessage(error.message);
      
      // Call error callback
      this.onSaveError(error);
      
      throw error;
    }
  }

  /**
   * Show saving indicator
   */
  showSavingIndicator() {
    const saveButton = document.getElementById('save-changes-btn');
    if (saveButton) {
      saveButton.disabled = true;
      saveButton.innerHTML = 'Saving...';
    }
  }

  /**
   * Show success message
   */
  showSuccessMessage() {
    const saveButton = document.getElementById('save-changes-btn');
    if (saveButton) {
      saveButton.disabled = false;
      saveButton.innerHTML = 'Saved!';
      
      // Reset button text after 2 seconds
      setTimeout(() => {
        saveButton.innerHTML = 'Save Changes';
      }, 2000);
    }
  }

  /**
   * Show error message
   */
  showErrorMessage(message) {
    const saveButton = document.getElementById('save-changes-btn');
    if (saveButton) {
      saveButton.disabled = false;
      saveButton.innerHTML = 'Save Changes';
    }
    
    // Create error notification
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.innerHTML = `Error: ${message}`;
    document.body.appendChild(notification);
    
    // Remove notification after 5 seconds
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 5000);
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ContentEditor;
}
