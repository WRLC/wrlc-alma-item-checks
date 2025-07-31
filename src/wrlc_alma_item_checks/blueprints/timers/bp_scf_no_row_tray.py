"""Timer trigger to re-check SCF No Row/Tray items"""
import logging
import azure.functions as func
from datetime import datetime, timezone

from wrlc_alma_api_client.models.item import Item

from src.wrlc_alma_item_checks.config import SCF_NO_ROW_TRAY_CHECK_NAME
from src.wrlc_alma_item_checks.services.storage_service import StorageService
from src.wrlc_alma_item_checks.handlers.scf_no_row_tray import SCFNoRowTray
from src.wrlc_alma_item_checks.handlers.scf_shared import SCFShared
from src.wrlc_alma_item_checks.handlers.scf_no_row_tray_report import ScfNoRowTrayReport

bp = func.Blueprint()


# Schedule to run every day at 9:00 AM UTC
@bp.schedule(schedule="0 0 9 * * *", arg_name="dailyTimer", run_on_startup=False)
def DailyScfReportTimer(dailyTimer: func.TimerRequest) -> None:
    """
    Timer-triggered function to process staged items and send a daily digest.
    """
    if dailyTimer.past_due:
        logging.warning("The timer is past due!")

    logging.info(f"Daily SCF Report Timer triggered at: {datetime.now(timezone.utc)}")

    storage_service = StorageService()
    table_name = "ScfNoRowTray"

    # 1. Get all staged items for this check from the table
    staged_items = storage_service.get_entities(
        table_name, filter_query=f"PartitionKey eq '{SCF_NO_ROW_TRAY_CHECK_NAME}'"
    )

    if not staged_items:
        logging.info(f"No items staged for {SCF_NO_ROW_TRAY_CHECK_NAME}. Exiting.")
        return

    # 2. Check if items should still be processed
    items_still_failing = []
    processed_barcodes = []

    for entity in staged_items:
        barcode = entity['RowKey']
        processed_barcodes.append(barcode)

        # ----- Shared Item Checks ----- #
        scf_shared: SCFShared = SCFShared(barcode)  # Create SCFShared instance from item
        item_data: Item | None = scf_shared.should_process()  # check if item should be processed

        if isinstance(item_data, Item):  # if item present, continue processing
            scf_no_row_tray: SCFNoRowTray = SCFNoRowTray(item_data)  # Create SCFNoRowTray instance from item

            if scf_no_row_tray.should_process():  # if item still fails validation, report it
                items_still_failing.append(scf_no_row_tray.item)

    # 3. Generate notification for items still failing validation
    if items_still_failing:
        scf_no_row_tray_report = ScfNoRowTrayReport()
        scf_no_row_tray_report.process(items_still_failing)

    # 4. Clean up all processed items from the staging table
    logging.info(f"Cleaning up {len(processed_barcodes)} processed items from table '{table_name}'.")
    for barcode in processed_barcodes:
        storage_service.delete_entity(table_name, partition_key=SCF_NO_ROW_TRAY_CHECK_NAME, row_key=barcode)
