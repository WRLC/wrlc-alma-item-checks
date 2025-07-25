# **WRLC Alma Item Checks Azure Functions**

This project contains an Azure Functions application designed to manage data and automate tasks related to Alma item checks for WRLC.

## **Features**

* **Alma Webhooks:** HTTP trigger functions for Alma integration profiles webhook URLs triggered on every item update.
* **Automated item fixes**: In some cases when an issue is discovered, the function will try to fix it automatically.
* **Email Notifications:** Sends email notifications when issues are discovered and/or fixed.

## Required Environment Variables

* `SQLALCHEMY_CONNECTION_STRING`: Database connection string
* `NOTIFIER_QUEUE_NAME`: Name of queue in function's storage account where notifications will be triggered
* `NOTIFIER_CONTAINER_NAME`: Name of container in function's storage account where notification content is stored
* `ACS_SENDER_CONTAINER_NAME`: Name of container in the acs-email-sender storage account where email content will be stored.

## Local Development

### Prerequisites

* Python 3.12+ 
* Poetry (for dependency management)
* [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python)
* [Azurite local storage emulator](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio%2Cblob-storage)
* [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer)
* [WRLC/acs-email-sender](https://github.com/WRLC/acs-email-sender)

### Setup and Configuration

1. **Clone repository:**
    ```bash
    git clone https://github.com/WRLC/wrlc-alma-item-checks.git
    cd wrlc-alma-item-checks
    ```

2. **Install dependencies:**
    ```bash
    poetry install
   source .venv/bin/activate
    ```

3. **Configure local settings:**
    Copy `local.settings.json` from template:
    ```bash
    cp local.settings.json.template local.settings.json
    ```
    Set environment variables in `local.settings.json`:

    * `SQLALCHEMY_CONNECTION_STRING`
    * `NOTIFIER_QUEUE_NAME`
    * `NOTIFIER_CONTAINER_NAME`
    * `ACS_SENDER_CONTAINER_NAME`
    * `ACS_SENDER_CONNECTION_STRING`
    * `SCF_DUPLICATES_SCHEDULE`
    * `SCF_DUPLICATES_CHECK_NAME`
    * `SCF_WEBHOOK_SECRET`

4. Start local function:
    ```bash
    azurite
    func start
    ```

## **Deployment**

Deployment to Azure is automated via GitHub Actions. The process utilizes deployment slots (e.g., stage and production) to ensure zero-downtime updates.

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.