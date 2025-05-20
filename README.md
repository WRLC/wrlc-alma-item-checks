# **WRLC Alma Item Checks Azure Functions**

This project contains an Azure Functions application designed to manage data and automate tasks related to Alma item checks for WRLC. It includes a CRUD API for managing checks, users, and notifications, as well as other scheduled/triggered functions.

## **Features**

* **CRUD API:** A RESTful API built with FastAPI for managing Check, User, and Notification data stored in a relational database (MySQL/PostgreSQL via SQLAlchemy).  
* **Database Persistence:** Uses SQLAlchemy as an ORM with a repository pattern for database interactions.  
* **Database Migrations:** Managed using Alembic.  
* **Scheduled/Triggered Functions:** Includes other Azure Functions for tasks like sending notifications and processing webhooks.  
* **Azure Storage Integration:** Utilizes Azure Blob Storage and Queue Storage (via Azurite locally).  
* **Email Notifications:** Sends emails via Azure Communication Services (implied by dependencies).  
* **Deployment:** Configured for deployment to Azure Functions via GitHub Actions.

## **Deployment**

The project is configured for deployment to Azure Functions using the GitHub Actions workflow located in .github/workflows/azure-functions-app-python.yml.

Ensure you have configured the necessary GitHub Secrets, such as AZURE\_FUNCTIONAPP\_PUBLISH\_PROFILE.

## **API Documentation**

When running the function app locally (func start) or deployed to Azure, the FastAPI integration automatically provides interactive API documentation:

* **Swagger UI:** Accessible at /api/docs  
* **ReDoc:** Accessible at /api/redoc

These interfaces allow you to explore the available endpoints, their parameters, request/response models, and even test the API directly from your browser.

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.