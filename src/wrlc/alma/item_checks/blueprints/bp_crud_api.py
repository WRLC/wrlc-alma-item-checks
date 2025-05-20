"""FastAPI app blueprint for Azure Functions"""
import azure.functions as func
from azure.functions import AsgiMiddleware
from src.wrlc.alma.item_checks.api.main import crud_api_app

bp_api = func.Blueprint()


@bp_api.route(
    route="{*remaining_path}",
    methods=[
        func.HttpMethod.GET,
        func.HttpMethod.POST,
        func.HttpMethod.PUT,
        func.HttpMethod.DELETE,
        func.HttpMethod.OPTIONS,
        func.HttpMethod.PATCH,
        func.HttpMethod.HEAD,
    ],
    auth_level=func.AuthLevel.FUNCTION
)
async def fastapi_handler(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """
    FastAPI app blueprint for Azure Functions

    Args:
        req (func.HttpRequest): the request object
        context (func.Context): the context object

    Returns:
        func.HttpResponse: the response object
    """
    return await AsgiMiddleware(crud_api_app).handle_async(req, context)
