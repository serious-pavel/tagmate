# TagMate

This project is a simple and convenient hashtag organizer and helper for social media posts. You could also edit your posts here and combine your tags in groups. This is
a **Django Framework** application. It includes a **PostgreSQL database**, and **Docker-based deployment**.

## How to Set Up and Run the Project Locally

Follow these steps to copy and run the **TagMate** project on your local development machine.

### Clone the Repository

```sh
git clone https://github.com/serious-pavel/tagmate.git
cd tagmate
```
### Set Up Environment Variables
Edit the .env file and update variables if needed:
 - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for Authentication through Google Application
 - `SU_EMAIL` and `SU_UID` for creating a superuser, this gives you access to Admin panel and other superuser features (SU_UID is an ID for your Google account in Google Application, unique for every Application)
```sh
cat .env.test > .env
```
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