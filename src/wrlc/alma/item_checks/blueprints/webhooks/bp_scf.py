"""Blueprint for Alma Item Update Webhook."""
import json
import logging
# noinspection PyPackageRequirements
import azure.functions as func
# noinspection PyPackageRequirements
from azure.functions import Blueprint
from src.wrlc.alma.item_checks.handlers.scf_no_x import SCFNoX
# noinspection PyPackageRequirements
from wrlc.alma.api_client.models.item import Item
import src.wrlc.alma.item_checks.config as config
from src.wrlc.alma.item_checks.utils.security import validate_webhook_signature

bp = Blueprint()


@bp.route('scfwebhook', methods=['GET', 'POST'])
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
    if not validate_webhook_signature(req.get_body(), config.SCF_WEBHOOK_SECRET, req.headers.get("X-Exl-Signature")):
        return func.HttpResponse("Invalid signature", status_code=401)

    # ----- Parse Item ----- #
    try:
        item: Item = Item(**req.get_json()['item'])  # Parse incoming JSON into Item

    except ValueError as e:  # Catch JSON decoding errors specifically
        logging.error(f"Error processing JSON request: {e}")
        return func.HttpResponse("Invalid JSON format", status_code=400)
    except Exception as e:
        logging.error(f"Unexpected error processing request: {e}", exc_info=True)  # Log traceback
        return func.HttpResponse("Error processing request", status_code=500)

    # ----- No X in barcode ----- #
    scf_no_x: SCFNoX = SCFNoX(item)  # Create SCFNoX instance from item

    if isinstance(scf_no_x.should_process(), Item):  # Check if SCFNoX should be processed
        scf_no_x.process(scf_no_x.should_process())  # If so, process it

    return func.HttpResponse("Webhook received", status_code=200)  # Return 200 OK
