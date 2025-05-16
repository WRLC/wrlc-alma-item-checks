"""Webhook for Alma Item Update"""
# noinspection PyPackageRequirements
import azure.functions as func
from src.wrlc.alma.item_checks.blueprints.webhooks.bp_scf import bp as scf_bp
from src.wrlc.alma.item_checks.blueprints.bp_notifier import bp as notifier_bp
# from src.wrlc.alma.item_checks.blueprints.bp_scfduplicates import bp as scfduplicates_bp

app = func.FunctionApp()

# Register the blueprints
app.register_blueprint(scf_bp)
app.register_blueprint(notifier_bp)
# app.register_blueprint(scfduplicates_bp)
