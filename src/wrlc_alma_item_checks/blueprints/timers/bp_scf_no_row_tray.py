"""Timer trigger to re-check SCF No Row/Tray items"""
import json
import logging
from typing import Any, Union
import uuid

import azure.functions as func
from datetime import datetime, timezone
from wrlc_alma_api_client.models.item import Item

from src.wrlc_alma_item_checks.config import (
    NOTIFIER_CONTAINER_NAME,
    SCF_NO_ROW_TRAY_CHECK_NAME,
    SCF_NO_ROW_TRAY_PROCESSOR_QUEUE_NAME,
    SCF_NO_ROW_TRAY_RESULTS_TABLE_NAME,
    SCF_NO_ROW_TRAY_SCHEDULE
)
from src.wrlc_alma_item_checks.services.storage_service import StorageService
from src.wrlc_alma_item_checks.handlers.scf_no_row_tray import SCFNoRowTray
from src.wrlc_alma_item_checks.handlers.scf_shared import SCFShared
from src.wrlc_alma_item_checks.handlers.scf_no_row_tray_report import ScfNoRowTrayReport

bp: func.Blueprint = func.Blueprint()


@bp.schedule(schedule=SCF_NO_ROW_TRAY_SCHEDULE, arg_name="dailyTimer", run_on_startup=False)
@bp.queue_output(
    arg_name="out_msg",
    queue_name=SCF_NO_ROW_TRAY_PROCESSOR_QUEUE_NAME,
    connection="AzureWebJobsStorage"
)
def DailyScfReportTimer(dailyTimer: func.TimerRequest, out_msg: func.Out[str]) -> None:
    """THE STARTER: Timer-triggered function to kick off the processing of staged items.
 
    This function gets all staged barcodes and places a single message on a queue
    to start a batch processing workflow. It runs very quickly and will not time out.
    """
    if dailyTimer.past_due:
        logging.warning(msg="The timer is past due!")

    logging.info(msg=f"DailyScfReportTimer: Daily SCF Report Timer triggered at: {datetime.now(timezone.utc)}")

    storage_service: StorageService = StorageService()

    # 1. Get all staged items for this check from the table
    staged_items: list[dict[str, Any]] = storage_service.get_entities(
        table_name=SCF_NO_ROW_TRAY_CHECK_NAME,
        filter_query=f"PartitionKey eq '{SCF_NO_ROW_TRAY_CHECK_NAME}'"
    )

    if not staged_items:
        logging.info(msg=f"DailyScfReportTimer: No items staged for {SCF_NO_ROW_TRAY_CHECK_NAME}. Exiting.")
        return

    run_id: str = str(uuid.uuid4())

    # 2. Store the full list of original entities in a blob for final cleanup
    original_entities_blob_name = f"{run_id}-original-entities.json"
    storage_service.upload_blob_data(
        container_name=NOTIFIER_CONTAINER_NAME,
        blob_name=original_entities_blob_name,
        data=staged_items
    )
    logging.info(f"DailyScfReportTimer: Stored original entities in blob '{original_entities_blob_name}'.")

    # 3. Create a temporary table to store results for this run
    results_table_name: str = f"{SCF_NO_ROW_TRAY_RESULTS_TABLE_NAME}{run_id.replace('-', '')}"
    storage_service.create_table_if_not_exists(results_table_name)
    logging.info(f"DailyScfReportTimer: Created results table '{results_table_name}' for run_id '{run_id}'.")

    # 4. Create the initial message to start the batch processing
    barcodes_to_process: list[str] = [entity['RowKey'] for entity in staged_items]

    # Store the barcodes to process in their own blob to keep the initial message small
    barcodes_blob_name = f"{run_id}-barcodes-to-process.json"
    storage_service.upload_blob_data(
        container_name=NOTIFIER_CONTAINER_NAME,
        blob_name=barcodes_blob_name,
        data=barcodes_to_process
    )
    logging.info(f"DailyScfReportTimer: Stored barcodes to process in blob '{barcodes_blob_name}'.")

    initial_message: dict[str, Any] = {
        "run_id": run_id,
        "results_table_name": results_table_name,
        "container_name": NOTIFIER_CONTAINER_NAME,
        "original_entities_blob_name": original_entities_blob_name,
        "barcodes_to_process_blob_name": barcodes_blob_name,
        "offset": 0  # Start at the beginning of the list
    }

    # 5. Send the message to the queue to be picked up by the "Worker"
    out_msg.set(json.dumps(initial_message))
    logging.info(
        f"DailyScfReportTimer: Queued processing for {len(barcodes_to_process)} items with run_id '{run_id}'."
    )


@bp.queue_trigger(
     arg_name="in_msg",
     queue_name=SCF_NO_ROW_TRAY_PROCESSOR_QUEUE_NAME,
     connection="AzureWebJobsStorage"
 )
@bp.queue_output(
    arg_name="out_msg",
    queue_name=SCF_NO_ROW_TRAY_PROCESSOR_QUEUE_NAME,
    connection="AzureWebJobsStorage"
)
def ProcessScfNoRowTrayQueue(in_msg: func.QueueMessage, out_msg: func.Out[str]) -> None:
    """THE WORKER: Processes items from the SCF No Row/Tray check in batches.

    This function is triggered by a queue message, processes a small batch of items,
    and then re-queues a message to process the next batch until all items are done.
    """
    logging.info("ProcessScfNoRowTrayQueue: Queue trigger function processed a message.")

    storage_service: StorageService = StorageService()

    # --- Parse message ---
    try:
        message: dict[str, Any] = json.loads(in_msg.get_body().decode())
        run_id: str = message["run_id"]
        results_table_name: str = message["results_table_name"]
        container_name: str = message["container_name"]
        original_entities_blob_name: str = message["original_entities_blob_name"]
        barcodes_to_process_blob_name: str = message["barcodes_to_process_blob_name"]
        offset: int = message["offset"]
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"ProcessScfNoRowTrayQueue: Error parsing queue message: {e}")
        return

    # 1. Download the full list of barcodes from the blob
    try:
        all_barcodes: list[str] = storage_service.download_blob_as_json(
            container_name=container_name, blob_name=barcodes_to_process_blob_name
        )
    except Exception as e:
        logging.error(
            f"Run ID '{run_id}': Failed to download barcode list from blob '{barcodes_to_process_blob_name}'. "
            f"Aborting. Error: {e}"
        )
        return

    # 2. Determine the current batch of barcodes to process using the offset
    batch_size = 50  # Process 50 items per invocation
    barcodes_for_this_batch: list[str] = all_barcodes[offset:offset + batch_size]
    new_offset = offset + len(barcodes_for_this_batch)

    logging.info(
        f"Run ID '{run_id}': Processing batch of {len(barcodes_for_this_batch)} items. "
        f"Offset: {offset}, Total: {len(all_barcodes)}."
    )

    # 3. Process the current batch
    for barcode in barcodes_for_this_batch:
        scf_shared: SCFShared = SCFShared(barcode=barcode)
        item_data: Union[Item, None] = scf_shared.should_process()

        if isinstance(item_data, Item):
            scf_no_row_tray: SCFNoRowTray = SCFNoRowTray(item=item_data)
            if scf_no_row_tray.should_process():
                # Item still fails, save it to the temporary results table
                result_entity: dict[str, str] = {
                    "PartitionKey": run_id,
                    "RowKey": barcode,
                    "ItemData": item_data.model_dump_json()
                }
                storage_service.upsert_entity(results_table_name, result_entity)

    # 4. Decide whether to continue or finish
    if new_offset < len(all_barcodes):
        # --- More items to process, queue the next batch ---
        next_message: dict[str, Any] = {
            "run_id": run_id,
            "results_table_name": results_table_name,
            "container_name": container_name,
            "original_entities_blob_name": original_entities_blob_name,
            "barcodes_to_process_blob_name": barcodes_to_process_blob_name,
            "offset": new_offset
        }
        out_msg.set(json.dumps(next_message))
        logging.info(f"Run ID '{run_id}': Queued next batch. New offset: {new_offset}.")
    else:
        # --- FINAL BATCH: All items processed, now generate report and clean up ---
        logging.info(f"Run ID '{run_id}': Final batch complete. Generating report and cleaning up.")

        # Get all failing items from the results table
        failing_entities: list[dict[str, Any]] = storage_service.get_entities(
            results_table_name, filter_query=f"PartitionKey eq '{run_id}'"
        )
        items_still_failing: list[Item] = [Item.model_validate_json(entity['ItemData']) for entity in failing_entities]

        if items_still_failing:
            report_handler: ScfNoRowTrayReport = ScfNoRowTrayReport()
            report_handler.process(items_still_failing=items_still_failing)

        # Clean up the original staged items using the efficient batch delete
        # Download the original list from the blob created by the starter function
        original_entities: list[dict[str, Any]] = storage_service.download_blob_as_json(
            container_name=container_name, blob_name=original_entities_blob_name
        )
        storage_service.delete_entities_batch(SCF_NO_ROW_TRAY_CHECK_NAME, original_entities)

        # Clean up the temporary results table
        storage_service.delete_table(results_table_name)

        # Clean up the temporary blobs
        storage_service.delete_blob(container_name, original_entities_blob_name)
        storage_service.delete_blob(container_name, barcodes_to_process_blob_name)
        logging.info(f"Run ID '{run_id}': Cleanup complete. Process finished.")
