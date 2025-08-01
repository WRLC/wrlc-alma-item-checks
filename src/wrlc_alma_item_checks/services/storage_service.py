"""Storage Helpers for Azure Blob and Queue Services"""
import logging
from azure.core.paging import ItemPaged
from typing import Dict, List, Union, Optional

from azure.data.tables import TableServiceClient, UpdateMode, TableClient
from azure.storage.blob import BlobServiceClient, ContentSettings, BlobClient, ContainerClient, BlobProperties
from azure.storage.queue import QueueServiceClient, QueueClient, TextBase64EncodePolicy
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

from src.wrlc_alma_item_checks.config import STORAGE_CONNECTION_STRING
from src.wrlc_alma_item_checks.services.data_service import DataService


# noinspection PyMethodMayBeStatic
class StorageService:
    """Service for Azure Storage operations."""
    def __init__(self):
        self.data_service: DataService = DataService()

    def get_blob_service_client(self) -> BlobServiceClient:
        """Returns an authenticated BlobServiceClient instance."""
        try:
            return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        except ValueError as e:
            logging.error(msg=f"StorageService.get_blob_service_client: Invalid storage connection string format: {e}")
            raise ValueError(f"Invalid storage connection string format: {e}") from e

    def get_queue_service_client(self) -> QueueServiceClient:
        """Returns an authenticated QueueServiceClient instance."""
        try:
            # Note: Functions often expect Base64 encoding for queue triggers/outputs.
            # Adjust policy if needed based on your specific binding configurations.
            # If using raw strings, set message_encode_policy=None, message_decode_policy=None.
            return QueueServiceClient.from_connection_string(
                conn_str=STORAGE_CONNECTION_STRING,
                message_encode_policy=TextBase64EncodePolicy()  # Encodes outgoing messages to Base64
            )
        except ValueError as e:
            logging.error(msg=f"StorageService.get_queue_service_client: Invalid storage connection string format: {e}")
            raise ValueError(f"Invalid storage connection string format: {e}") from e

    def get_table_service_client(self) -> TableServiceClient:
        """Returns an authenticated TableServiceClient instance."""
        try:
            return TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
        except ValueError as e:
            logging.error(
                msg=f"StorageService.get_table_service_client: Invalid storage connection string format for Table "
                    f"Service: {e}"
            )
            raise ValueError(f"Invalid storage connection string format for Table Service: {e}") from e

    def get_queue_client(self, queue_name: str) -> QueueClient:
        """
        Returns an authenticated QueueClient for a specific queue.
        Does NOT automatically create the queue.
        """
        if not queue_name:
            logging.error(msg="StorageService.get_queue_client: Queue name cannot be empty.")
            raise ValueError("Queue name cannot be empty.")
        try:
            # Inherits policy from service client if created that way, or specify explicitly
            return QueueClient.from_connection_string(
                STORAGE_CONNECTION_STRING,
                queue_name,
                message_encode_policy=TextBase64EncodePolicy()
            )
        except ValueError as e:
            logging.error(
                msg=f"StorageService.get_queue_client: Invalid storage connection string or queue name "
                    f"'{queue_name}': {e}"
            )
            raise ValueError(f"Invalid storage connection string or queue name '{queue_name}': {e}") from e

    def upload_blob_data(
            self, container_name: str, blob_name: str, data: Union[str, bytes, Dict, List], overwrite: bool = True
    ):
        """
        Uploads data to Azure Blob Storage. Serializes Python dicts/lists to JSON.

        Args:
            container_name: The name of the blob container.
            blob_name: The name of the blob.
            data: The data to upload (str, bytes, dict, or list).
            overwrite: Whether to overwrite the blob if it already exists.

        Raises:
            ValueError: If container or blob name is invalid.
            TypeError: If data type is not supported.
            azure.core.exceptions.ServiceRequestError: For network issues.
            azure.core.exceptions.ResourceExistsError: If blob exists and overwrite is False.
        """
        if not container_name or not blob_name:
            logging.error(msg="StorageService.upload_blob_data: Container name and blob name cannot be empty.")
            raise ValueError("Container name and blob name cannot be empty.")

        logging.debug(
            msg=f"StorageService.upload_blob_data: Attempting to upload blob to {container_name}/{blob_name} "
                f"(overwrite={overwrite})"
        )
        try:
            blob_client: BlobClient = self.get_blob_service_client().get_blob_client(
                container=container_name,
                blob=blob_name
            )
        except ValueError as e:  # Catch connection string format error from getter
            logging.error(
                msg=f"StorageService.upload_blob_data: Failed to get blob client for {container_name}/{blob_name}: {e}"
            )
            raise

        data_service: DataService = DataService()

        try:
            upload_data: Union[str, bytes]
            settings_to_pass: Optional[ContentSettings] = None

            if isinstance(data, (dict, list)):
                upload_data: bytes = data_service.serialize_data(data=data).encode()
                settings_to_pass: ContentSettings = ContentSettings(content_type='application/json')

            elif isinstance(data, str):
                upload_data: bytes = data.encode()
                settings_to_pass: ContentSettings = ContentSettings(content_type='text/plain; charset=utf-8')

            elif isinstance(data, bytes):
                upload_data: bytes = data
            else:
                logging.error(
                    msg=f"StorageService.upload_blob_data: Unsupported data type for upload_blob_data: {type(data)}"
                )
                raise TypeError(f"Unsupported data type for upload_blob_data: {type(data)}")

            blob_client.upload_blob(
                data=upload_data,
                blob_type="BlockBlob",
                overwrite=overwrite,
                content_settings=settings_to_pass
            )

            logging.info(
                msg=f"StorageService.upload_blob_data: Successfully uploaded blob: {container_name}/{blob_name}"
            )

        except ResourceExistsError as e:
            if not overwrite:
                logging.warning(
                    msg=f"StorageService.upload_blob_data: Blob {container_name}/{blob_name} already exists and "
                        f"overwrite is False."
                )
                raise
            else:
                logging.error(
                    msg=f"StorageService.upload_blob_data: Unexpected ResourceExistsError despite overwrite=True for "
                        f"{container_name}/{blob_name}: {e}"
                )
                raise
        except Exception as e:
            logging.error(
                msg=f"StorageService.upload_blob_data: Failed to upload blob {container_name}/{blob_name}: {e}"
            )
            raise

    def download_blob_as_text(self, container_name: str, blob_name: str, encoding: str = 'utf-8') -> str:
        """
        Downloads blob content as a decoded text string.

        Args:
            container_name: The name of the blob container.
            blob_name: The name of the blob.
            encoding: The encoding to use for decoding the blob bytes.

        Returns:
            The decoded string content of the blob.

        Raises:
            ValueError: If container or blob name is invalid.
            azure.core.exceptions.ResourceNotFoundError: If the blob does not exist.
            azure.core.exceptions.ServiceRequestError: For network issues.
        """
        if not container_name or not blob_name:
            logging.error(msg="StorageService.download_blob_as_text: Container name and blob name cannot be empty.")
            raise ValueError("Container name and blob name cannot be empty.")

        logging.debug(
            msg=f"StorageService.download_blob_as_text: Attempting to download blob as text from "
                f"{container_name}/{blob_name}"
        )

        blob_client: BlobClient = self.get_blob_service_client().get_blob_client(
            container=container_name,
            blob=blob_name
        )

        try:
            blob_content_bytes: bytes = blob_client.download_blob().readall()
            logging.info(
                msg=f"StorageService.download_blob_as_text: Successfully downloaded blob: {container_name}/{blob_name}"
            )
            return blob_content_bytes.decode(encoding=encoding)
        except ResourceNotFoundError:
            logging.error(msg=f"StorageService.download_blob_as_text: Blob not found: {container_name}/{blob_name}")
            raise
        except UnicodeDecodeError as e:
            logging.error(
                msg=f"StorageService.download_blob_as_text: Failed to decode blob {container_name}/{blob_name} "
                    f"using encoding '{encoding}': {e}"
            )
            raise e
        except Exception as e:
            logging.error(
                msg=f"StorageService.download_blob_as_text: Failed to download blob {container_name}/{blob_name} "
                    f"as text: {e}"
            )
            raise

    def download_blob_as_json(self, container_name: str, blob_name: str, encoding: str = 'utf-8') -> Union[Dict, List]:
        """
        Downloads blob content and parses it as JSON.

        Args:
            container_name: The name of the blob container.
            blob_name: The name of the blob.
            encoding: The encoding of the stored text data before JSON parsing.

        Returns:
            A Python dictionary or list parsed from the blob's JSON content.

        Raises:
            ValueError: If container or blob name is invalid.
            DataSerializationError: If the content cannot be parsed as JSON.
            azure.core.exceptions.ResourceNotFoundError: If the blob does not exist.
            azure.core.exceptions.ServiceRequestError: For network issues.
        """
        text_content: str = self.download_blob_as_text(
            container_name=container_name,
            blob_name=blob_name,
            encoding=encoding
        )

        try:
            return self.data_service.deserialize_data(text_content)
        except Exception as e:
            logging.error(
                msg=f"StorageService.download_blob_as_json: Failed to parse blob content from "
                    f"{container_name}/{blob_name} as JSON: {e}"
            )
            raise

    def list_blobs(self, container_name: str, name_starts_with: Optional[str] = None) -> List[str]:
        """
        Lists blob names in a container, optionally filtering by prefix.

        Args:
            container_name: The name of the blob container.
            name_starts_with: Optional prefix to filter blob names.

        Returns:
            A list of blob names matching the criteria. Returns empty list if
            container not found.

        Raises:
            ValueError: If container name is invalid.
            azure.core.exceptions.ServiceRequestError: For network issues.
        """
        if not container_name:
            logging.error(msg="StorageService.list_blobs: Container name cannot be empty.")
            raise ValueError("Container name cannot be empty.")

        logging.debug(
            msg=f"StorageService.list_blobs: Listing blobs in container '{container_name}' starting with "
                f"'{name_starts_with or ''}'"
        )
        try:
            container_client: ContainerClient = self.get_blob_service_client().get_container_client(
                container=container_name
            )
            blob_items: ItemPaged[BlobProperties] = container_client.list_blobs(name_starts_with=name_starts_with)
            blob_names: List[str] = [blob.name for blob in blob_items]
            logging.info(
                msg=f"StorageService.list_blobs: Found {len(blob_names)} blobs in '{container_name}' matching prefix "
                    f"'{name_starts_with or ''}'."
            )
            return blob_names
        except ResourceNotFoundError:
            logging.warning(
                msg=f"StorageService.list_blobs: Container '{container_name}' not found while listing blobs."
            )
            return []
        except Exception as e:
            logging.error(msg=f"StorageService.list_blobs: Failed to list blobs in container '{container_name}': {e}")
            raise

    def delete_blob(self, container_name: str, blob_name: str):
        """
        Deletes a specific blob. Does not raise error if blob doesn't exist.

        Args:
            container_name: The name of the blob container.
            blob_name: The name of the blob to delete.

        Raises:
            ValueError: If container or blob name is invalid.
            azure.core.exceptions.ServiceRequestError: For network issues.
        """
        if not container_name or not blob_name:
            logging.error(msg="StorageService.delete_blob: Container name and blob name cannot be empty.")
            raise ValueError("Container name and blob name cannot be empty.")

        logging.debug(msg=f"StorageService.delete_blob: Attempting to delete blob: {container_name}/{blob_name}")
        blob_client: BlobClient = self.get_blob_service_client().get_blob_client(
            container=container_name,
            blob=blob_name
        )
        try:
            blob_client.delete_blob(delete_snapshots="include")
            logging.info(msg=f"StorageService.delete_blob: Successfully deleted blob: {container_name}/{blob_name}")
        except ResourceNotFoundError:
            logging.warning(
                msg=f"StorageService.delete_blob: Blob not found during deletion, presumed already deleted: "
                    f"{container_name}/{blob_name}"
            )
        except Exception as e:
            logging.error(msg=f"StorageService.delete_blob: Failed to delete blob {container_name}/{blob_name}: {e}")
            raise

    def send_queue_message(self, queue_name: str, message_content: Union[Dict, List, str]):
        """
        Sends a message to the specified Azure Queue. Serializes dicts/lists to JSON.

        Args:
            queue_name: The name of the target queue.
            message_content: The message content (dict, list, or string).

        Raises:
            ValueError: If queue name is invalid.
            TypeError: If message_content type is not supported.
            azure.core.exceptions.ServiceRequestError: For network issues.
        """
        if not queue_name:
            logging.error(msg="StorageService.send_queue_message: Queue name cannot be empty.")
            raise ValueError("Queue name cannot be empty.")

        message_str: str
        try:
            if isinstance(message_content, (dict, list)):
                message_str = self.data_service.serialize_data(data=message_content)
            elif isinstance(message_content, str):
                message_str = message_content
            else:
                logging.error(
                    msg=f"StorageService.send_queue_message: Unsupported message content type: {type(message_content)}"
                )
                raise TypeError(f"Unsupported message content type: {type(message_content)}")

            logging.debug(
                msg=f"StorageService.send_queue_message: Attempting to send message to queue '{queue_name}': "
                    f"{message_str[:100]}..."
            )
            queue_client: QueueClient = self.get_queue_client(queue_name=queue_name)
            queue_client.send_message(content=message_str)
            logging.info(msg=f"StorageService.send_queue_message: Successfully sent message to queue '{queue_name}'")

        except Exception as e:
            logging.error(
                msg=f"StorageService.send_queue_message: Failed to send message to queue '{queue_name}': {e}"
            )
            raise

    def get_entities(self, table_name: str, filter_query: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Retrieves entities from a specified Azure Table, with an optional filter.

        Args:
            table_name: The name of the table to query.
            filter_query: An OData filter string to apply to the query.
                          If None, all entities in the table are returned.
                          Example: "PartitionKey eq 'some_key'"

        Returns:
            A list of dictionaries, where each dictionary is an entity.
            Returns an empty list if the table does not exist.

        Raises:
            ValueError: If table_name is invalid.
            azure.core.exceptions.ServiceRequestError: For network or other service issues.
        """
        if not table_name:
            logging.error(msg="StorageService.get_entities: Table name cannot be empty.")
            raise ValueError("Table name cannot be empty.")

        logging.debug(
            msg=f"StorageService.get_entities: Querying entities from table '{table_name}' with filter: "
                f"'{filter_query or 'All'}'"
        )
        try:
            table_client: TableClient = self.get_table_service_client().get_table_client(table_name=table_name)

            entities: List[Dict[str, any]] = list(table_client.query_entities(query_filter=filter_query))

            logging.info(
                msg=f"StorageService.get_entities: Retrieved {len(entities)} entities from table '{table_name}'."
            )
            return entities

        except ResourceNotFoundError:
            logging.warning(
                msg=f"StorageService.get_entities: Table '{table_name}' not found while querying entities. "
                    f"Returning empty list."
            )
            return []
        except Exception as e:
            logging.error(
                msg=f"StorageService.get_entities: Failed to query entities from table '{table_name}': {e}",
                exc_info=True
            )
            raise

    def delete_entity(self, table_name: str, partition_key: str, row_key: str):
        """
        Deletes a specific entity from an Azure Table.
        Does not raise an error if the entity does not exist.

        Args:
            table_name: The name of the target table.
            partition_key: The PartitionKey of the entity to delete.
            row_key: The RowKey of the entity to delete.

        Raises:
            ValueError: If any of the key arguments are invalid.
            azure.core.exceptions.ServiceRequestError: For network or other service issues.
        """
        if not all([table_name, partition_key, row_key]):
            logging.error(msg="StorageService.delete_entity: Table name, partition key, and row key cannot be empty.")
            raise ValueError("Table name, partition key, and row key cannot be empty.")

        logging.debug(
            msg=f"StorageService.delete_entity: Attempting to delete entity from {table_name} "
                f"with PK='{partition_key}' and RK='{row_key}'"
        )
        try:
            table_client: TableClient = self.get_table_service_client().get_table_client(table_name=table_name)
            table_client.delete_entity(partition_key=partition_key, row_key=row_key)
            logging.info(
                msg=f"StorageService.delete_entity: Successfully deleted entity from {table_name} with RowKey "
                    f"'{row_key}'."
            )
        except ResourceNotFoundError:
            logging.warning(
                msg=f"StorageService.delete_entity: Entity not found during deletion, presumed already deleted: "
                f"Table='{table_name}', PK='{partition_key}', RK='{row_key}'"
            )
        except Exception as e:
            logging.error(
                msg=f"StorageService.delete_entity: Failed to delete entity from {table_name} with "
                    f"RowKey '{row_key}': {e}",
                exc_info=True
            )
            raise

    def upsert_entity(self, table_name: str, entity: Dict[str, any]):
        """
        Inserts or updates an entity in the specified Azure Table.
        Creates the table if it does not exist.

        Args:
            table_name: The name of the target table.
            entity: A dictionary representing the entity to upsert.
                    Must contain 'PartitionKey' and 'RowKey'.

        Raises:
            ValueError: If table_name is invalid or entity is missing required keys.
            azure.core.exceptions.ServiceRequestError: For network or other service issues.
        """
        if not table_name:
            logging.error(msg="StorageService.upsert_entity: Table name cannot be empty.")
            raise ValueError("Table name cannot be empty.")
        if not all(k in entity for k in ["PartitionKey", "RowKey"]):
            logging.error(msg="Entity must contain 'PartitionKey' and 'RowKey'.")
            raise ValueError("Entity must contain 'PartitionKey' and 'RowKey'.")

        logging.debug(msg=f"StorageService.upsert_entity: Attempting to upsert entity into table '{table_name}'")
        try:
            table_client: TableClient = self.get_table_service_client().get_table_client(table_name)

            try:
                table_client.create_table()
                logging.info(msg=f"StorageService.upsert_entity: Table '{table_name}' did not exist and was created.")
            except ResourceExistsError:
                pass

            table_client.upsert_entity(entity=entity, mode=UpdateMode.REPLACE)
            logging.info(
                msg=f"StorageService.upsert_entity: Successfully upserted entity with RowKey '{entity.get('RowKey')}' "
                    f"into table '{table_name}'."
            )

        except Exception as e:
            logging.error(
                msg=f"StorageService.upsert_entity: Failed to upsert entity into table '{table_name}': {e}",
                exc_info=True
            )
            raise
