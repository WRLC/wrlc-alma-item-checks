"""Webhook for Alma Item Update"""
# noinspection PyPackageRequirements
import azure.functions as func
from src.wrlc.alma.item_checks.blueprints.webhooks.bp_scf import bp as scf_bp
from src.wrlc.alma.item_checks.blueprints.bp_notifier import bp as notifier_bp
from src.wrlc.alma.item_checks.blueprints.bp_scfduplicates import bp as scfduplicates_bp
# from src.wrlc.alma.item_checks.blueprints.bp_crud_api import bp_api

app = func.FunctionApp()

# Register the blueprints
app.register_blueprint(scf_bp)  # SCF Webhook
app.register_blueprint(notifier_bp)  # Notifier Queue Trigger
app.register_blueprint(scfduplicates_bp)  # SCF Duplicates Timer Trigger
# app.register_blueprint(bp_api)  # FastAPI CRUD app
