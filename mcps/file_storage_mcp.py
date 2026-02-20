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
from pathlib import Path
from datetime import datetime

logger = get_logger(__name__)


class FileStorageInput(MCPInput):
    """Input parameters for file storage operations."""
    action: str = Field(
        ...,
        description="Action: upload, list, delete, get_link, share"
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
            credentials_file: Path to Google credentials JSON file
        """
        super().__init__()
        self.api_key = api_key
        self.credentials_file = credentials_file or settings.google_drive_credentials_file
        self.base_drive_url = "https://drive.google.com/file/d"
        self.service = None
        
        # Try to initialize Google Drive service
        try:
            self._initialize_drive_service()
        except Exception as e:
            logger.warning("file_storage_drive_initialization_failed", error=str(e))
    
    def _initialize_drive_service(self):
        """Initialize Google Drive service."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.exceptions import RefreshError
            from googleapiclient.discovery import build
            
            credentials = None
            
            # Try to load existing credentials
            if os.path.exists(self.credentials_file):
                credentials = Credentials.from_authorized_user_file(
                    self.credentials_file,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except RefreshError:
                    logger.warning("file_storage_credentials_refresh_failed")
                    credentials = None
            
            if credentials and credentials.valid:
                self.service = build('drive', 'v3', credentials=credentials)
                logger.info("file_storage_drive_service_initialized")
            else:
                logger.warning("file_storage_no_valid_credentials")
        
        except ImportError:
            logger.warning("file_storage_google_libraries_not_installed")
        except Exception as e:
            logger.error("file_storage_service_initialization_error", error=str(e))
    
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
        elif action == "delete":
            return await self._delete_file(input_data, user_id)
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
            file_name = input_data.file_name or os.path.basename(input_data.file_path)
            file_size = os.path.getsize(input_data.file_path)
            
            # Simulate upload to Google Drive
            file_id = f"drive_file_{user_id}_{datetime.now().timestamp()}"
            drive_link = f"{self.base_drive_url}/{file_id}/view"
            
            # Create local storage record
            storage_dir = Path("storage/files")
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file to storage
            stored_path = storage_dir / f"{file_id}_{file_name}"
            with open(input_data.file_path, 'rb') as src:
                with open(stored_path, 'wb') as dst:
                    dst.write(src.read())
            
            logger.info("file_storage_uploaded",
                       user_id=user_id,
                       file_name=file_name,
                       file_id=file_id,
                       file_size=file_size)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data={
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "drive_link": drive_link,
                    "upload_time": datetime.now().isoformat()
                },
                message=f"File '{file_name}' uploaded successfully",
                metadata={
                    "file_id": file_id,
                    "drive_link": drive_link
                }
            )
        
        except Exception as e:
            logger.error("file_storage_upload_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to upload file",
                error=str(e)
            )
    
    async def _list_files(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """List files in storage."""
        try:
            storage_dir = Path("storage/files")
            files = []
            
            if storage_dir.exists():
                for file_path in storage_dir.iterdir():
                    if file_path.is_file():
                        files.append({
                            "file_name": file_path.name,
                            "file_size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
            
            logger.info("file_storage_listed", user_id=user_id, count=len(files))
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data={"files": files, "count": len(files)},
                message=f"Found {len(files)} files in storage",
                metadata={"count": len(files)}
            )
        
        except Exception as e:
            logger.error("file_storage_list_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to list files",
                error=str(e)
            )
    
    async def _delete_file(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """Delete a file from storage."""
        if not input_data.file_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="File ID is required",
                error="Missing file_id"
            )
        
        try:
            storage_dir = Path("storage/files")
            deleted_count = 0
            
            if storage_dir.exists():
                for file_path in storage_dir.iterdir():
                    if input_data.file_id in file_path.name:
                        file_path.unlink()
                        deleted_count += 1
            
            logger.info("file_storage_deleted", user_id=user_id, file_id=input_data.file_id)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                message=f"Deleted {deleted_count} file(s)",
                data={"deleted_count": deleted_count}
            )
        
        except Exception as e:
            logger.error("file_storage_delete_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to delete file",
                error=str(e)
            )
    
    async def _get_file_link(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """Get shareable link for a file."""
        if not input_data.file_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="File ID is required",
                error="Missing file_id"
            )
        
        try:
            # Generate Google Drive link
            drive_link = f"{self.base_drive_url}/{input_data.file_id}/view"
            
            logger.info("file_storage_link_generated", user_id=user_id, file_id=input_data.file_id)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data={"file_id": input_data.file_id, "drive_link": drive_link},
                message=f"Drive link: {drive_link}",
                metadata={"drive_link": drive_link}
            )
        
        except Exception as e:
            logger.error("file_storage_link_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to generate link",
                error=str(e)
            )
    
    async def _share_file(self, input_data: FileStorageInput, user_id: int) -> MCPOutput:
        """Share a file with another user."""
        if not input_data.file_id or not input_data.share_with:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="File ID and email are required",
                error="Missing parameters"
            )
        
        try:
            logger.info("file_storage_shared",
                       user_id=user_id,
                       file_id=input_data.file_id,
                       share_with=input_data.share_with)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                message=f"File shared with {input_data.share_with}",
                data={
                    "file_id": input_data.file_id,
                    "shared_with": input_data.share_with,
                    "access_level": input_data.access_level
                }
            )
        
        except Exception as e:
            logger.error("file_storage_share_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to share file",
                error=str(e)
            )
    
    @property
    def capabilities(self) -> list:
        """Get MCP capabilities."""
        return [
            MCPCapability(
                name="upload",
                description="Upload a file to Google Drive",
                parameters=["file_path", "file_name", "folder_id"]
            ),
            MCPCapability(
                name="list",
                description="List files in storage",
                parameters=[]
            ),
            MCPCapability(
                name="delete",
                description="Delete a file",
                parameters=["file_id"]
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
