import requests
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import os
import mimetypes

from uuid import UUID

@dataclass
class IntentService:        

    def create_intent(
        self,
        user_id: str = "dce043c3-6786-40c5-956c-69a65a9fb772",
        image_uuid: Optional[str] = None,
        taker_id: Optional[str] = None,
        max_amount_usd: Optional[float] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        uuid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an intent by making a POST request to Supabase.
        
        Args:
            user_id: UUID of the user (defaults to provided user ID)
            taker_id: Optional UUID of the taker
            max_amount_usd: Optional maximum amount in USD
            description: Optional description text
            status: Optional intent status
            uuid: Optional UUID for the intent
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = "https://wasidcejmcpfvlblkkqg.supabase.co/rest/v1/intents"
        
        headers = {
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indhc2lkY2VqbWNwZnZsYmxra3FnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE2Mzg0MywiZXhwIjoyMDc4NzM5ODQzfQ.h49728IyVlYmZ5LVot4_53tqt5iTltevPc2p1OQ_3IU",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
                
        # Build payload with only provided fields
        payload = {}
        
        if uuid:
            payload["uuid"] = uuid
        if image_uuid:
            payload["image_uuid"] = image_uuid
        if user_id:
            payload["user_id"] = user_id
        if taker_id:
            payload["taker_id"] = taker_id
        if max_amount_usd is not None:
            payload["max_amount_usd"] = max_amount_usd
        if description:
            payload["description"] = description
        if status:
            payload["status"] = status
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Failed to create intent: {str(e)}")

    def upload_image(
        self,
        image_uuid: str,
        image_data: Union[str, bytes]
    ) -> Dict[str, Any]:
        """
        Upload an image to Supabase storage.
        
        Args:
            image_uuid: The UUID/filename for the image (e.g., "image-uuid.jpg")
            image_data: Either a file path (str) or image bytes (bytes)
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            FileNotFoundError: If image_data is a path and file doesn't exist
        """
        url = f"https://wasidcejmcpfvlblkkqg.supabase.co/storage/v1/object/intent-images/{image_uuid}"
        
        # Handle image_data - either file path or bytes
        if isinstance(image_data, str):
            # It's a file path
            if not os.path.exists(image_data):
                raise FileNotFoundError(f"Image file not found: {image_data}")
            
            with open(image_data, 'rb') as f:
                image_bytes = f.read()
            
            # Determine content type from file extension
            content_type, _ = mimetypes.guess_type(image_data)
            if not content_type or not content_type.startswith('image/'):
                # Fallback to common image types
                ext = os.path.splitext(image_data)[1].lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(ext, 'image/jpeg')
        else:
            # It's already bytes
            image_bytes = image_data
            
            # Try to determine content type from image_uuid extension
            content_type, _ = mimetypes.guess_type(image_uuid)
            if not content_type or not content_type.startswith('image/'):
                ext = os.path.splitext(image_uuid)[1].lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(ext, 'image/jpeg')
        
        api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indhc2lkY2VqbWNwZnZsYmxra3FnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE2Mzg0MywiZXhwIjoyMDc4NzM5ODQzfQ.h49728IyVlYmZ5LVot4_53tqt5iTltevPc2p1OQ_3IU"
        
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
            "x-upsert": "true"  # Allow overwriting if file exists
        }
        
        try:
            response = requests.post(url, headers=headers, data=image_bytes)
            response.raise_for_status()
            return response.json() if response.content else {"status": "success"}
        except requests.exceptions.HTTPError as e:
            error_msg = f"Failed to upload image: {str(e)}"
            if e.response is not None:
                error_msg += f" - Status: {e.response.status_code}"
                try:
                    error_msg += f" - Response: {e.response.text}"
                except:
                    pass
            raise requests.exceptions.RequestException(error_msg)
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Failed to upload image: {str(e)}")