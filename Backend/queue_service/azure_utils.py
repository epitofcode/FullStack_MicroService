import os
import structlog
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

log = structlog.get_logger()
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
UPLOADS_CONTAINER = os.getenv("AZURE_STORAGE_UPLOADS_CONTAINER", "uploads")
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING) if CONNECTION_STRING else None

def generate_sas_upload_url(blob_name: str, expiration_hours: int = 1) -> str | None:
    if not blob_service_client:
        log.error("Azure Blob Service Client not initialized. Check connection string.")
        return None
    try:
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=UPLOADS_CONTAINER,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(hours=expiration_hours)
        )
        url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{UPLOADS_CONTAINER}/{blob_name}?{sas_token}"
        log.info("Generated Azure Blob SAS URL.", blob_name=blob_name)
        return url
    except Exception as e:
        log.error("Failed to generate Azure Blob SAS URL.", error=str(e))
        return None