"""Blueprint for Alma Item Update Webhook."""
import json
import logging
import os

import azure.functions as func
from wrlc_alma_api_client.models.item import Item  # type: ignore

from src.wrlc_alma_item_checks.config import SCF_WEBHOOK_SECRET
from src.wrlc_alma_item_checks.handlers.scf_no_row_tray import SCFNoRowTray
from src.wrlc_alma_item_checks.handlers.scf_shared import SCFShared
from src.wrlc_alma_item_checks.handlers.scf_no_x import SCFNoX
from src.wrlc_alma_item_checks.utils.security import validate_webhook_signature

bp = func.Blueprint()


@bp.route('scfwebhook', methods=['GET', 'POST'], auth_level='anonymous')
def ScfWebhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Webhook endpoint for handling SCF IZ Item Update events.

    Args:
        req (func.HttpRequest): The incoming HTTP request.

    Returns:
        func.HttpResponse: The HTTP response.
    """
    if req.method != 'POST':
        if req.params.get("challenge"):
            challenge_response = {"challenge": req.params.get("challenge")}
            return func.HttpResponse(
                json.dumps(challenge_response),
                mimetype="application/json",
                status_code=200
            )
        return func.HttpResponse("Hello World", status_code=200)

    # ----- Validate Signature ----- #
    is_local_dev = os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT") == "Development"

    if not is_local_dev:
        if not validate_webhook_signature(req.get_body(), SCF_WEBHOOK_SECRET, req.headers.get("X-Exl-Signature")):
            logging.warning("Invalid webhook signature received.")
            return func.HttpResponse("Invalid signature", status_code=403)

    # ----- Parse Item ----- #
    try:
        request_data = req.get_json()
        barcode = request_data.get("item", {}).get("item_data", {}).get("barcode")

        if not barcode:
            logging.error("Barcode not found in webhook payload.")

            return func.HttpResponse("Invalid payload: Barcode is missing.", status_code=400)

    except ValueError:  # Catches req.get_json() errors

        logging.error("Error processing JSON request: Invalid JSON format.")
        return func.HttpResponse("Invalid JSON format", status_code=400)

    except Exception as e:  # Catches other errors
        logging.error(f"Unexpected error processing request: {e}", exc_info=True)
        return func.HttpResponse("Error processing request", status_code=500)

    # ----- Shared Item Checks ----- #
    scf_shared: SCFShared = SCFShared(barcode)  # Create SCFShared instance from barcode
    item_data: Item | None = scf_shared.should_process()  # check if item should be processed

    if isinstance(item_data, Item):  # if item present, continue processing

        # ----- No X in barcode ----- #
        scf_no_x: SCFNoX = SCFNoX(item_data)  # Create SCFNoX instance from item
        scf_no_x.should_process()  # Check if SCFNoX should be processed

        # ----- Incorrect or No Row/Tray information ----- #
        scf_no_row_tray: SCFNoRowTray = SCFNoRowTray(item_data)  # Create SCFNoRowTray instance from item

        if scf_no_row_tray.should_process():  # if item should be re-processed, stage it for daily report
            scf_no_row_tray.stage()

        # ----- Withdrawn Item ----- #
        # scf_withdrawn: SCFWithdrawn = SCFWithdrawn(item_data)

        # if scf_withdrawn.should_process():
        #    scf_withdrawn.process()

    return func.HttpResponse("Webhook received", status_code=200)  # Return 200 OK
