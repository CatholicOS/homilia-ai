"""
S3 Service for Homilia AI
Handles all AWS S3 operations for file storage and retrieval.
"""

import os
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import mimetypes
from urllib.parse import urlparse
import dotenv

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


class S3Service:
    """Service class for AWS S3 operations."""
    
    def __init__(self):
        """Initialize S3 service with environment variables."""
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            raise ValueError("Missing required AWS credentials or S3 bucket name in environment variables")
        
        # Configure S3 client with retry settings
        config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            region_name=self.aws_region
        )
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                config=config
            )
            
            # Verify bucket exists and is accessible
            self._verify_bucket_access()
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def _verify_bucket_access(self) -> bool:
        """Verify that the bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' not found")
                raise ValueError(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'")
                raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                logger.error(f"Error accessing S3 bucket: {str(e)}")
                raise
    
    def upload_file(self, file_path: str, s3_key: str, 
                   content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local file path to upload
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Additional metadata to store with the file
            
        Returns:
            Dict containing upload result information
        """
        try:
            # Determine content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare extra args
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Get file info
            file_info = self.get_file_info(s3_key)
            
            logger.info(f"Successfully uploaded file to S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': file_info.get('size', 0),
                'content_type': content_type,
                'last_modified': file_info.get('last_modified'),
                'etag': file_info.get('etag')
            }
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {'success': False, 'error': 'File not found'}
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def upload_bytes(self, file_bytes: bytes, s3_key: str,
                    content_type: Optional[str] = None,
                    metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload bytes data to S3.
        
        Args:
            file_bytes: Bytes data to upload
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the data
            metadata: Additional metadata to store with the file
            
        Returns:
            Dict containing upload result information
        """
        try:
            # Determine content type if not provided
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Prepare extra args
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload bytes
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes,
                **extra_args
            )
            
            # Get file info
            file_info = self.get_file_info(s3_key)
            
            logger.info(f"Successfully uploaded bytes to S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'file_size': len(file_bytes),
                'content_type': content_type,
                'last_modified': file_info.get('last_modified'),
                'etag': file_info.get('etag')
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload bytes to S3: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error uploading bytes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def download_file(self, s3_key: str, local_path: str) -> Dict[str, Any]:
        """
        Download a file from S3 to local filesystem.
        
        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
            
        Returns:
            Dict containing download result information
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            
            # Get file size
            file_size = os.path.getsize(local_path)
            
            logger.info(f"Successfully downloaded file from S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                'local_path': local_path,
                'file_size': file_size
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"File not found in S3: {s3_key}")
                return {'success': False, 'error': 'File not found'}
            else:
                logger.error(f"Failed to download file from S3: {str(e)}")
                return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error downloading file: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_file_bytes(self, s3_key: str) -> Dict[str, Any]:
        """
        Get file content as bytes from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dict containing file bytes and metadata
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            file_bytes = response['Body'].read()
            
            logger.info(f"Successfully retrieved file bytes from S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                'file_bytes': file_bytes,
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"File not found in S3: {s3_key}")
                return {'success': False, 'error': 'File not found'}
            else:
                logger.error(f"Failed to get file bytes from S3: {str(e)}")
                return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting file bytes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            Dict containing deletion result information
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            logger.info(f"Successfully deleted file from S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                'message': 'File deleted successfully'
            }
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_files(self, s3_keys: List[str]) -> Dict[str, Any]:
        """
        Delete multiple files from S3.
        
        Args:
            s3_keys: List of S3 object keys to delete
            
        Returns:
            Dict containing deletion result information
        """
        try:
            if not s3_keys:
                return {'success': True, 'deleted': [], 'errors': []}
            
            # Prepare delete objects
            delete_objects = [{'Key': key} for key in s3_keys]
            
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': delete_objects}
            )
            
            deleted = [obj['Key'] for obj in response.get('Deleted', [])]
            errors = response.get('Errors', [])
            
            logger.info(f"Successfully deleted {len(deleted)} files from S3")
            return {
                'success': True,
                'deleted': deleted,
                'errors': errors,
                'total_requested': len(s3_keys),
                'total_deleted': len(deleted)
            }
            
        except ClientError as e:
            logger.error(f"Failed to delete files from S3: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error deleting files: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        Get file metadata from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dict containing file metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'success': True,
                's3_key': s3_key,
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {}),
                'storage_class': response.get('StorageClass'),
                'server_side_encryption': response.get('ServerSideEncryption')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"File not found in S3: {s3_key}")
                return {'success': False, 'error': 'File not found'}
            else:
                logger.error(f"Failed to get file info from S3: {str(e)}")
                return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting file info: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> Dict[str, Any]:
        """
        List files in S3 bucket with optional prefix filter.
        
        Args:
            prefix: S3 key prefix to filter files
            max_keys: Maximum number of files to return
            
        Returns:
            Dict containing list of files and metadata
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                PaginationConfig={'MaxItems': max_keys}
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append({
                            's3_key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'etag': obj['ETag'],
                            'storage_class': obj.get('StorageClass')
                        })
            
            logger.info(f"Successfully listed {len(files)} files from S3")
            return {
                'success': True,
                'files': files,
                'count': len(files),
                'prefix': prefix
            }
            
        except ClientError as e:
            logger.error(f"Failed to list files from S3: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error listing files: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600, 
                         http_method: str = 'GET') -> Dict[str, Any]:
        """
        Generate a presigned URL for S3 object access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method for the URL (GET, PUT, etc.)
            
        Returns:
            Dict containing presigned URL and metadata
        """
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod=f'{http_method.lower()}_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Successfully generated presigned URL for: {s3_key}")
            return {
                'success': True,
                'url': url,
                's3_key': s3_key,
                'expiration': expiration,
                'http_method': http_method,
                'expires_at': datetime.utcnow() + timedelta(seconds=expiration)
            }
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def copy_file(self, source_key: str, dest_key: str, 
                 metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Copy a file within S3 bucket.
        
        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key
            metadata: Additional metadata for the copied file
            
        Returns:
            Dict containing copy result information
        """
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
                extra_args['MetadataDirective'] = 'REPLACE'
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key,
                **extra_args
            )
            
            logger.info(f"Successfully copied file from {source_key} to {dest_key}")
            return {
                'success': True,
                'source_key': source_key,
                'dest_key': dest_key,
                'message': 'File copied successfully'
            }
            
        except ClientError as e:
            logger.error(f"Failed to copy file in S3: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error copying file: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking file existence: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {str(e)}")
            return False
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """
        Get information about the S3 bucket.
        
        Returns:
            Dict containing bucket information
        """
        try:
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Get bucket location
            location_response = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            location = location_response.get('LocationConstraint', 'us-east-1')
            
            return {
                'success': True,
                'bucket_name': self.bucket_name,
                'region': location,
                'creation_date': response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('date')
            }
            
        except ClientError as e:
            logger.error(f"Failed to get bucket info: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting bucket info: {str(e)}")
            return {'success': False, 'error': str(e)}


# Utility functions for common operations
def generate_s3_key(parish_id: str, document_type: str, filename: str) -> str:
    """
    Generate a standardized S3 key for parish documents.
    
    Args:
        parish_id: Parish identifier
        document_type: Type of document (homily, bulletin, etc.)
        filename: Original filename
        
    Returns:
        S3 key string
    """
    # Sanitize filename
    safe_filename = filename.replace(' ', '_').replace('/', '_')
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    return f"parishes/{parish_id}/{document_type}/{timestamp}_{safe_filename}"


def get_file_extension_from_key(s3_key: str) -> str:
    """
    Extract file extension from S3 key.
    
    Args:
        s3_key: S3 object key
        
    Returns:
        File extension (including dot)
    """
    return os.path.splitext(s3_key)[1]


def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate if file type is allowed.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed file extensions
        
    Returns:
        True if file type is allowed, False otherwise
    """
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in [ext.lower() for ext in allowed_extensions]


# Common file type configurations for the Homilia AI project
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.aac']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv']
