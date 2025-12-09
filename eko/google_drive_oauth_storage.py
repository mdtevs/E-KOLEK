"""
OAuth-based Google Drive Storage for Django
This uses personal Google account instead of service account to avoid storage quota issues
"""
import os
import io
import mimetypes
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible
import logging

logger = logging.getLogger(__name__)

@deconstructible
class GoogleDriveOAuthStorage(Storage):
    """
    Google Drive Storage using OAuth (personal account) instead of service account
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_file=None, folder_id=None):
        self.credentials_file = credentials_file or getattr(settings, 'GOOGLE_DRIVE_OAUTH_CREDENTIALS_FILE', None)
        self.token_file = getattr(settings, 'GOOGLE_DRIVE_TOKEN_FILE', os.path.join(settings.BASE_DIR, 'google-drive-token.pickle'))
        self.folder_id = folder_id or getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        self._service = None
        
    @property
    def service(self):
        """Get or create Google Drive service using OAuth"""
        if self._service is None:
            try:
                creds = None
                
                # Load existing token
                if os.path.exists(self.token_file):
                    with open(self.token_file, 'rb') as token:
                        creds = pickle.load(token)
                
                # If no valid credentials, initiate OAuth flow
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        if not self.credentials_file or not os.path.exists(self.credentials_file):
                            raise Exception(f"OAuth credentials file not found: {self.credentials_file}")
                        
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    
                    # Save credentials for next run
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)
                
                self._service = build('drive', 'v3', credentials=creds)
                logger.info("Google Drive OAuth service initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing Google Drive OAuth service: {e}")
                raise
                
        return self._service
    
    def _save(self, name, content):
        """Save file to Google Drive using OAuth"""
        try:
            # Extract just the filename from the path (remove reward_images/ prefix)
            import os
            clean_filename = os.path.basename(name)
            
            # Prepare file metadata
            file_metadata = {
                'name': clean_filename,  # Use clean filename without path
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(clean_filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Prepare file content
            file_content = content.read()
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=False
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            # Set file permissions to be publicly viewable
            self.service.permissions().create(
                fileId=file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            logger.info(f"File uploaded to Google Drive via OAuth: {name} (ID: {file['id']})")
            return file['id']
            
        except Exception as e:
            logger.error(f"Error uploading file to Google Drive via OAuth: {e}")
            raise
    
    def _open(self, name, mode='rb'):
        """Open file from Google Drive"""
        try:
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
    
    def url(self, name):
        """Get public URL for full-size image that works with HTML img tags"""
        # Use Google's content delivery URL which works best for images
        # Format: https://lh3.googleusercontent.com/d/{file_id}
        # This works with public files and is optimized for embedding
        return f"https://lh3.googleusercontent.com/d/{name}"
    
    def size(self, name):
        """Get file size"""
        try:
            file_info = self.service.files().get(fileId=name, fields='size').execute()
            return int(file_info.get('size', 0))
        except:
            return 0
