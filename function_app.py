"""Webhook for Alma Item Update"""
import azure.functions as func
from src.wrlc_alma_item_checks.blueprints.timers.bp_scf_duplicates import bp as scfduplicates_bp
from src.wrlc_alma_item_checks.blueprints.timers.bp_scf_no_row_tray import bp as scfno_row_tray
from src.wrlc_alma_item_checks.blueprints.webhooks.bp_scf import bp as scf_bp
from src.wrlc_alma_item_checks.blueprints.bp_notifier import bp as notifier_bp

app = func.FunctionApp()

# Register the blueprints
app.register_blueprint(scfduplicates_bp)  # SCF Duplicates Timer Trigger
app.register_blueprint(scfno_row_tray)  # SCF No Row/Tray Timer Trigger
app.register_blueprint(scf_bp)  # SCF Webhook
app.register_blueprint(notifier_bp)  # Notifier Queue Trigger
