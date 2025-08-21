# TagMate

This project is a simple and convenient hashtag organizer and helper for social media posts. You could also edit your posts here and combine your tags in groups. This is
a **Django Framework** application. It includes a **PostgreSQL database**, and **Docker-based deployment**.

This application allows only authentication through social accounts (only Google for now), you can't create or use a local account.

## ⚠️ IMPORTANT ⚠️

If you started your project before any `tag` that is presented in the project, you need to conduct a transition to the newest version following this [instruction](#transition-to-the-newest-version).

## How to Set Up and Run the Project Locally

Follow these steps to copy and run the **TagMate** project on your local development machine.

### Clone the Repository

```sh
git clone https://github.com/serious-pavel/tagmate.git
cd tagmate
```
### Set Up Environment Variables
Edit the .env file and update variables if needed.
```sh
cat .env.test > .env
```
###### Database and application parameters
**Required**.

You can leave `DB_NAME` `DB_USER` `DB_PASS` `SECRET_KEY` with default values for the local development needs. Please change for productive deployment.

The new SECRET KEY could be generated with the following command:

```python
from django.core.management.utils import get_random_secret_key  
get_random_secret_key()
```
###### Google OAuth Application
**Required**.

`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are secrets for Google's OAuth service, you can create your own authentication application or use credentials for existing one.
###### Admin Panel Access
**Optional**.

`SU_EMAIL` and `SU_UID` are credentials for a superuser that is created during deployment.
`SU_EMAIL` is your gmail. `SU_UID` is an ID for your Google account in Google's OAuth service Application, unique for every Application.
This gives you access to the Admin panel and other superuser features. If you don't need it skip the step.

You can build and deploy all containers, start a Django app, find your uid in the Profile tab (http://127.0.0.1:8000/profile). Set it as `SU_UID` and re-deploy docker app container. This should update your user and grant it superuser rights.

### Build and Start the Containers
```sh
docker-compose build
docker-compose up -d
```
### Access the Application
 - Base URL: http://127.0.0.1:8000/
 - Admin Panel: http://127.0.0.1:8000/admin/ (or available directly on the main page)
### Running Tests & Code Checks
```sh
docker-compose run --rm app sh -c "python manage.py test"
docker-compose run --rm app sh -c "flake8"
```
## Transition to the newest version

### 1. Backup data

This step is **recommended**.

Run `backup.sh` script with parameters from `transition` folder.

You can take your container ids from `docker ps` output.

You can take your db_user and db_name from .env file.

You can tag\mark your backup folder with additional text.

```bash
sh transition/backup.sh <postgres_container_id> <app_container_id> <db_user> <db_name> [tag/mark]
```

### 2. Run migration

This is a **MANDATORY** step.

Technically, you’ll only need to run a `migrate` command after updating the project code to the latest state. However, if you want to run it as clean as possible, you should remove the existing containers and run a full deployment with build. The data will still be preserved on the volume.

#### Fast migration

```bash
docker-compose run --rm app sh -c "python manage.py migrate"
```

#### Clean migration

```bash
docker-compose down --remove-orphans
docker-compose up --build
```
