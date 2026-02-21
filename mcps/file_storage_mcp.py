"""
File Storage MCP for Google Drive integration.
Handles file uploads, storage, and link generation.
"""

from typing import Optional, Dict, Any
from pydantic import Field
from mcps.base import BaseMCP, MCPInput, MCPOutput, MCPStatus, MCPCapability
from utils.logger import get_logger
from config import settings
import os
import pickle
from pathlib import Path
from datetime import datetime

logger = get_logger(__name__)

# Google Drive API scopes
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']


class FileStorageInput(MCPInput):
    """Input parameters for file storage operations."""
    action: str = Field(
        ...,
        description="Action: upload, list, get_link, share"
    )
    file_path: Optional[str] = Field(default=None, description="Local file path to upload")
    file_name: Optional[str] = Field(default=None, description="Name for the file in storage")
    folder_id: Optional[str] = Field(default=None, description="Google Drive folder ID")
    file_id: Optional[str] = Field(default=None, description="Google Drive file ID")
    share_with: Optional[str] = Field(default=None, description="Email to share file with")
    access_level: Optional[str] = Field(default="viewer", description="Access level: viewer, commenter, editor")


class FileStorageMCP(BaseMCP):
    """MCP for Google Drive file storage."""
    
    def __init__(self, api_key: str = None, credentials_file: str = None):
        """
        Initialize File Storage MCP.
        
        Args:
            api_key: Google API key
            credentials_file: Path to Google Drive OAuth client secrets JSON file
        """
        super().__init__()
        self.api_key = api_key
        self.credentials_file = credentials_file or settings.google_drive_credentials_file
        self.token_path = Path("credentials/drive_token.pickle")
        self.base_drive_url = "https://drive.google.com/file/d"
        self.service = None
        
        # Try to initialize Google Drive service from saved token
        try:
            self._initialize_drive_service()
        except Exception as e:
            logger.warning("file_storage_drive_initialization_failed", error=str(e))
    
    def _initialize_drive_service(self):
        """Initialize Google Drive service from saved token or trigger OAuth."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            credentials = None
            
            # Load saved token if it exists
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    credentials = pickle.load(token)
            
            # Refresh if expired
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                    # Save refreshed token
                    with open(self.token_path, 'wb') as token:
                        pickle.dump(credentials, token)
                except Exception:
                    logger.warning("file_storage_credentials_refresh_failed")
                    credentials = None
            
            if credentials and credentials.valid:
                self.service = build('drive', 'v3', credentials=credentials)
                logger.info("file_storage_drive_service_initialized")
            else:
                logger.warning("file_storage_no_valid_token",
                              hint="Run: python auth_drive.py to authenticate Google Drive")
        
        except ImportError:
            logger.warning("file_storage_google_libraries_not_installed")
        except Exception as e:
            logger.error("file_storage_service_initialization_error", error=str(e))
    
    def authenticate(self) -> bool:
        """
        Run OAuth flow to authenticate with Google Drive.
        Must be called interactively (opens browser).
        
        Returns:
            True if authentication succeeded
        """
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            if not os.path.exists(self.credentials_file):
                logger.error("file_storage_credentials_file_missing", path=self.credentials_file)
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, DRIVE_SCOPES
            )
            credentials = flow.run_local_server(port=0)
            
            # Save token
            self.token_path.parent.mkdir(exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(credentials, token)
            
            # Build service
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("file_storage_drive_authenticated")
            return True
            
        except Exception as e:
            logger.error("file_storage_auth_failed", error=str(e))
            return False
    
    def is_authenticated(self) -> bool:
        """Check if Drive is authenticated."""
        if self.service:
            return True
        if self.token_path.exists():
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                    return creds and creds.valid
            except Exception:
                return False
        return False
    
    async def execute(self, input_data: FileStorageInput, user_id: int = None, **kwargs) -> MCPOutput:
        """
        Execute file storage operation.
        
        Args:
            input_data: Operation parameters
            user_id: Optional user ID
            **kwargs: Additional context
            
        Returns:
            MCPOutput with operation results
        """
        action = input_data.action.lower()
        
        if action == "upload":
            return await self._upload_file(input_data, user_id)
        elif action == "list":
            return await self._list_files(input_data, user_id)
        elif action == "get_link":
            return await self._get_file_link(input_data, user_id)
        elif action == "share":
            return await self._share_file(input_data, user_id)
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Unknown action: {action}",
                error="Invalid action"
            )
    
    async def _upload_file(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """Upload a file to Google Drive."""
        if not input_data.file_path:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="File path is required",
                error="Missing file_path"
            )
        
        if not os.path.exists(input_data.file_path):
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"File not found: {input_data.file_path}",
                error="File not found"
            )
        
        try:
            # Use user-specified name if provided, otherwise fall back to original filename
            file_name = input_data.file_name if input_data.file_name else os.path.basename(input_data.file_path)
            # Preserve original extension if user name doesn't have one
            if input_data.file_name and '.' not in input_data.file_name:
                original_ext = os.path.splitext(input_data.file_path)[1]
                if original_ext:
                    file_name = f"{input_data.file_name}{original_ext}"
            file_size = os.path.getsize(input_data.file_path)
            
            # Try Google Drive upload if authenticated
            if self.service or self._try_build_service():
                from googleapiclient.http import MediaFileUpload
                
                file_metadata = {'name': file_name}
                if input_data.folder_id:
                    file_metadata['parents'] = [input_data.folder_id]
                
                media = MediaFileUpload(input_data.file_path, resumable=True)
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink, webContentLink'
                ).execute()
                
                file_id = file.get('id')
                drive_link = file.get('webViewLink', f"{self.base_drive_url}/{file_id}/view")
                
                # Make file accessible via link
                self.service.permissions().create(
                    fileId=file_id,
                    body={'type': 'anyone', 'role': 'reader'}
                ).execute()
                
                logger.info("file_storage_uploaded_to_drive",
                           user_id=user_id, file_name=file_name,
                           file_id=file_id, file_size=file_size)
                
                return MCPOutput(
                    status=MCPStatus.SUCCESS,
                    data={
                        "file_id": file_id,
                        "file_name": file_name,
                        "file_size": file_size,
                        "drive_link": drive_link,
                        "upload_time": datetime.now().isoformat(),
                        "synced": True
                    },
                    message=f"✅ File '{file_name}' uploaded to Google Drive!\n📎 Link: {drive_link}",
                    metadata={"file_id": file_id, "drive_link": drive_link}
                )
            else:
                # Fallback: save locally
                storage_dir = Path("storage/files")
                storage_dir.mkdir(parents=True, exist_ok=True)
                
                local_id = f"local_{user_id}_{int(datetime.now().timestamp())}"
                stored_path = storage_dir / f"{local_id}_{file_name}"
                with open(input_data.file_path, 'rb') as src:
                    with open(stored_path, 'wb') as dst:
                        dst.write(src.read())
                
                logger.info("file_storage_uploaded_locally",
                           user_id=user_id, file_name=file_name, file_size=file_size)
                
                return MCPOutput(
                    status=MCPStatus.SUCCESS,
                    data={
                        "file_id": local_id,
                        "file_name": file_name,
                        "file_size": file_size,
                        "upload_time": datetime.now().isoformat(),
                        "synced": False
                    },
                    message=f"File '{file_name}' saved locally (Google Drive not authenticated - run: python auth_drive.py)",
                    metadata={"file_id": local_id}
                )
        
        except Exception as e:
            logger.error("file_storage_upload_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Failed to upload file: {str(e)}",
                error=str(e)
            )
    
    def _try_build_service(self) -> bool:
        """Try to build Drive service from saved token."""
        try:
            self._initialize_drive_service()
            return self.service is not None
        except Exception:
            return False
    
    async def _list_files(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """List files in Google Drive."""
        try:
            if self.service or self._try_build_service():
                results = self.service.files().list(
                    pageSize=20,
                    fields="files(id, name, size, modifiedTime, webViewLink, mimeType)",
                    orderBy="modifiedTime desc"
                ).execute()
                
                files = []
                for f in results.get('files', []):
                    files.append({
                        "file_id": f['id'],
                        "file_name": f['name'],
                        "file_size": f.get('size', 'N/A'),
                        "modified": f.get('modifiedTime', ''),
                        "drive_link": f.get('webViewLink', ''),
                        "mime_type": f.get('mimeType', '')
                    })
                
                # Build readable message
                if files:
                    msg_lines = [f"📁 Found {len(files)} files in Google Drive:\n"]
                    for i, f in enumerate(files, 1):
                        msg_lines.append(f"{i}. {f['file_name']}")
                    message = "\n".join(msg_lines)
                else:
                    message = "No files found in Google Drive."
                
                return MCPOutput(
                    status=MCPStatus.SUCCESS,
                    data={"files": files, "count": len(files)},
                    message=message,
                    metadata={"count": len(files)}
                )
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message="Google Drive not authenticated. Run: python auth_drive.py",
                    error="Not authenticated"
                )
        
        except Exception as e:
            logger.error("file_storage_list_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Failed to list files: {str(e)}",
                error=str(e)
            )
    
    async def _get_file_link(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """Get shareable link for a file. Supports lookup by file_id or file_name."""
        if not input_data.file_id and not input_data.file_name:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Please provide a file name or file ID.",
                error="Missing file_id and file_name"
            )
        
        try:
            if self.service or self._try_build_service():
                file_id = input_data.file_id
                file_name_found = None
                
                # If no file_id, search by file name
                if not file_id and input_data.file_name:
                    query = f"name contains '{input_data.file_name}' and trashed = false"
                    results = self.service.files().list(
                        q=query,
                        pageSize=5,
                        fields="files(id, name, webViewLink)"
                    ).execute()
                    files = results.get('files', [])
                    
                    if not files:
                        return MCPOutput(
                            status=MCPStatus.FAILURE,
                            message=f"No file found matching '{input_data.file_name}' in Google Drive.",
                            error="File not found"
                        )
                    
                    # Use the first match
                    file_id = files[0]['id']
                    file_name_found = files[0]['name']
                
                # Ensure file is shared publicly
                try:
                    self.service.permissions().create(
                        fileId=file_id,
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                except Exception:
                    pass  # Permission may already exist
                
                file = self.service.files().get(
                    fileId=file_id,
                    fields='id, name, webViewLink'
                ).execute()
                
                drive_link = file.get('webViewLink', f"{self.base_drive_url}/{file_id}/view")
                name = file_name_found or file.get('name', input_data.file_name)
                
                return MCPOutput(
                    status=MCPStatus.SUCCESS,
                    data={"file_id": file_id, "drive_link": drive_link, "file_name": name},
                    message=f"📎 Shareable link for '{name}': {drive_link}",
                    metadata={"drive_link": drive_link}
                )
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message="Google Drive not authenticated. Run: python auth_drive.py",
                    error="Not authenticated"
                )
        
        except Exception as e:
            logger.error("file_storage_link_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Failed to get link: {str(e)}",
                error=str(e)
            )
    
    async def _share_file(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """Share a file with another user. Supports lookup by file_id or file_name."""
        if not input_data.share_with:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Email address is required to share a file.",
                error="Missing share_with"
            )
        if not input_data.file_id and not input_data.file_name:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Please provide a file name or file ID.",
                error="Missing file_id and file_name"
            )
        
        try:
            if self.service or self._try_build_service():
                file_id = input_data.file_id
                file_name_found = None
                
                # If no file_id, search by file name
                if not file_id and input_data.file_name:
                    query = f"name contains '{input_data.file_name}' and trashed = false"
                    results = self.service.files().list(
                        q=query,
                        pageSize=5,
                        fields="files(id, name)"
                    ).execute()
                    files = results.get('files', [])
                    
                    if not files:
                        return MCPOutput(
                            status=MCPStatus.FAILURE,
                            message=f"No file found matching '{input_data.file_name}' in Google Drive.",
                            error="File not found"
                        )
                    
                    file_id = files[0]['id']
                    file_name_found = files[0]['name']
                
                role_map = {"viewer": "reader", "commenter": "commenter", "editor": "writer"}
                role = role_map.get(input_data.access_level, "reader")
                
                self.service.permissions().create(
                    fileId=file_id,
                    body={
                        'type': 'user',
                        'role': role,
                        'emailAddress': input_data.share_with
                    },
                    sendNotificationEmail=True
                ).execute()
                
                name = file_name_found or input_data.file_name or file_id
                logger.info("file_storage_shared_via_drive",
                           user_id=user_id, file_id=file_id,
                           share_with=input_data.share_with)
                
                return MCPOutput(
                    status=MCPStatus.SUCCESS,
                    message=f"✅ '{name}' shared with {input_data.share_with} as {input_data.access_level}",
                    data={
                        "file_id": file_id,
                        "shared_with": input_data.share_with,
                        "access_level": input_data.access_level
                    }
                )
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message="Google Drive not authenticated. Run: python auth_drive.py",
                    error="Not authenticated"
                )
        
        except Exception as e:
            logger.error("file_storage_share_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Failed to share file: {str(e)}",
                error=str(e)
            )
    
    def get_description(self) -> str:
        """Get MCP description."""
        return "File storage and Google Drive integration for uploading, sharing, and managing files"
    
    def get_capabilities(self) -> list:
        """Get MCP capabilities."""
        return [
            MCPCapability(
                name="upload",
                description="Upload a file to Google Drive with user-specified name",
                parameters=["file_path", "file_name", "folder_id"]
            ),
            MCPCapability(
                name="list",
                description="List files in Google Drive",
                parameters=[]
            ),
            MCPCapability(
                name="get_link",
                description="Get shareable Google Drive link",
                parameters=["file_id"]
            ),
            MCPCapability(
                name="share",
                description="Share file with another user",
                parameters=["file_id", "share_with", "access_level"]
            )
        ]
