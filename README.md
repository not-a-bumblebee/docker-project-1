# CIT3495 - Project 1: Data Collection and Analytics System
# Group 13

## Members:
Nicholas
Thuc

## Instructions
At the root of the project create a .env file and fill out values for the environment variables:

### Database Credentials
MYSQL_ROOT_PASSWORD=tbd
MYSQL_DATABASE=analytics_db   //kinda mandatory
MYSQL_USER=tbd
MYSQL_PASSWORD=tbd

### App Secrets
FLASK_SECRET_KEY=tbd
AUTH_TOKEN_SECRET=tbd

### Commands

To start containers
```
docker compose up -d --build
```

To Nuke containers and any stray data
```
docker compose down --volumes --remove-orphans
```

### Usage
got to http://localhost:5000/ and login with:
username: admin
password: password123