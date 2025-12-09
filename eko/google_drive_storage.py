import os
import io
import mimetypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible
import logging

logger = logging.getLogger(__name__)

@deconstructible
class GoogleDriveStorage(Storage):
    """
    Google Drive Storage backend for Django
    """
    
    def __init__(self, credentials_file=None, folder_id=None):
        self.credentials_file = credentials_file or getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS_FILE', None)
        self.folder_id = folder_id or getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        self._service = None
        
    @property
    def service(self):
        """Get or create Google Drive service"""
        if self._service is None:
            try:
                if self.credentials_file and os.path.exists(self.credentials_file):
                    credentials = Credentials.from_service_account_file(
                        self.credentials_file,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                    self._service = build('drive', 'v3', credentials=credentials)
                else:
                    logger.error("Google Drive credentials file not found or not configured")
                    raise Exception("Google Drive credentials not configured")
            except Exception as e:
                logger.error(f"Error initializing Google Drive service: {e}")
                raise
        return self._service
    
    def _save(self, name, content):
        """Save file to Google Drive"""
        try:
            # Ensure we have a folder ID
            if not self.folder_id:
                raise Exception("Google Drive folder ID not configured")
            
            # Prepare file metadata - make sure the file goes in YOUR folder
            file_metadata = {
                'name': name,
                'parents': [self.folder_id]  # This puts it in your shared folder
            }
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(name)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Prepare file content
            file_content = content.read()
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=False  # Try non-resumable upload first
            )
            
            # Upload file to your shared folder
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink,parents'
            ).execute()
            
            # Verify the file was created in the correct folder
            if self.folder_id not in file.get('parents', []):
                logger.warning(f"File may not be in the correct folder: {file}")
            
            # Set file permissions to be publicly viewable - CRITICAL for images to display
            try:
                permission = self.service.permissions().create(
                    fileId=file['id'],
                    body={
                        'role': 'reader',
                        'type': 'anyone',
                        'allowFileDiscovery': False
                    },
                    supportsAllDrives=True,
                    fields='id'
                ).execute()
                logger.info(f"✅ Public permission set for file: {file['id']} (Permission ID: {permission.get('id')})")
            except Exception as perm_error:
                logger.error(f"❌ Failed to set public permissions: {perm_error}")
                # This is critical - if permissions fail, the image won't be viewable
            
            logger.info(f"File uploaded to Google Drive: {name} (ID: {file['id']}) in folder {self.folder_id}")
            logger.info(f"WebContentLink: {file.get('webContentLink', 'N/A')}")
            return file['id']  # Return file ID as the "name"
            
        except Exception as e:
            logger.error(f"Error uploading file to Google Drive: {e}")
            # Instead of raising, fall back to local storage
            from django.core.files.storage import default_storage
            from django.core.files.storage import FileSystemStorage
            
            # Use local storage as fallback
            local_storage = FileSystemStorage()
            content.seek(0)  # Reset file pointer
            local_name = local_storage._save(name, content)
            logger.warning(f"Falling back to local storage for file: {name} -> {local_name}")
            return local_name
    
    def _open(self, name, mode='rb'):
        """Open file from Google Drive"""
        try:
            # Download file content
            file_content = self.service.files().get_media(fileId=name).execute()
            return ContentFile(file_content)
        except Exception as e:
            logger.error(f"Error opening file from Google Drive: {e}")
            raise
    
    def delete(self, name):
        """Delete file from Google Drive"""
        try:
            self.service.files().delete(fileId=name).execute()
            logger.info(f"File deleted from Google Drive: {name}")
        except Exception as e:
            logger.error(f"Error deleting file from Google Drive: {e}")
            raise
    
    def exists(self, name):
        """Check if file exists in Google Drive"""
        try:
            self.service.files().get(fileId=name).execute()
            return True
        except:
            return False
    
    def listdir(self, path):
        """List directory contents (not applicable for Google Drive)"""
        return [], []
    
    def size(self, name):
        """Get file size"""
        try:
            file_metadata = self.service.files().get(fileId=name, fields='size').execute()
            return int(file_metadata.get('size', 0))
        except:
            return 0
    
    def url(self, name):
        """Get public URL for full-size image"""
        try:
            # Use Google Drive's file view URL format
            # This works with public files and loads in img tags
            # Format: https://drive.google.com/file/d/{file_id}/view
            # Or use the uc format with id parameter which is more reliable for embedding
            if name and len(name) > 10:  # Likely a file ID
                # This format works best for embedding images
                return f"https://lh3.googleusercontent.com/d/{name}"
            
            return f"https://lh3.googleusercontent.com/d/{name}"
            
        except Exception as e:
            logger.error(f"Error getting URL for file {name}: {e}")
            return f"https://lh3.googleusercontent.com/d/{name}"
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system and
        available for new content to be written to.
        """
        return name
    
    def get_alternative_name(self, file_root, file_ext):
        """
        Return an alternative filename, by adding an underscore and a random 7
        character alphanumeric string (before the file extension, if one
        exists) to the filename.
        """
        import uuid
        return f"{file_root}_{uuid.uuid4().hex[:7]}{file_ext}"
