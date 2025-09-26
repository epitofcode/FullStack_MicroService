import os
import structlog
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

log = structlog.get_logger()

# These variables are loaded from the root .env file
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
UPLOADS_CONTAINER = os.getenv("AZURE_STORAGE_UPLOADS_CONTAINER", "uploads")
RESULTS_CONTAINER = os.getenv("AZURE_STORAGE_RESULTS_CONTAINER", "results")

# Initialize the client once. If the connection string is missing, it will be None.
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING) if CONNECTION_STRING else None

async def download_blob_to_path(blob_name: str, local_path: str) -> bool:
    """Downloads a blob from the 'uploads' container to a local temporary path."""
    if not blob_service_client:
        log.error("Azure Blob Service Client not initialized. Cannot download.")
        return False
    try:
        log.info("Downloading file from Azure Blob...", blob_name=blob_name)
        blob_client = blob_service_client.get_blob_client(container=UPLOADS_CONTAINER, blob=blob_name)
        
        with open(local_path, "wb") as download_file:
            stream = await blob_client.download_blob()
            data = await stream.readall()
            download_file.write(data)
            
        log.info("File downloaded successfully from Azure.", local_path=local_path)
        return True
    except ResourceNotFoundError:
        log.error("File not found in Azure Blob Storage.", blob_name=blob_name)
        return False
    except Exception as e:
        log.error("Failed to download file from Azure.", error=str(e), blob_name=blob_name)
        return False

async def upload_file_to_blob(local_path: str, blob_name: str) -> str | None:
    """Uploads a result file to the 'results' container and returns its URL."""
    if not blob_service_client:
        log.error("Azure Blob Service Client not initialized. Cannot upload.")
        return None
    try:
        log.info("Uploading result file to Azure Blob...", blob_name=blob_name)
        results_container_client = blob_service_client.get_container_client(RESULTS_CONTAINER)
        
        # Ensure the 'results' container exists. This is idempotent.
        try:
            await results_container_client.create_container()
            log.info(f"Container '{RESULTS_CONTAINER}' created.")
        except ResourceExistsError:
            pass # Container already exists, which is fine.
        except Exception as e:
            log.error("Failed to create 'results' container in Azure.", error=str(e))
            # Continue anyway, it might exist.

        blob_client = results_container_client.get_blob_client(blob=blob_name)
        with open(local_path, "rb") as data:
            await blob_client.upload_blob(data, overwrite=True)
        
        url = blob_client.url
        log.info("Result file uploaded successfully to Azure.", url=url)
        return url
    except Exception as e:
        log.error("Failed to upload result file to Azure.", error=str(e), blob_name=blob_name)
        return None