# Simon Connect - Flask Application

A secure Flask-based web application with JWT authentication for accessing Simon India's Software and Forms Hub.

## Features

- **Landing Page**: Beautiful landing page with navigation to different sections
- **Software Page**: Public access to view all company software (Proton, SPHERE, Smartinv)
- **Forms Hub**: Secure access to all company forms with JWT authentication
- **Employee Corner**: Coming soon page for employee resources

## Requirements

Python 3.7 or higher

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

Edit `.env` file to set your credentials and secret keys.

## Default Credentials

The application requires admin login (credentials can be changed in `.env`):

- **Username**: `admin` | **Password**: `admin123`

## Security Features

- JWT (JSON Web Token) authentication for Forms Hub
- Token expiration: 24 hours
- Secure session management
- Client-side token validation

## Pages

- `/` - Landing page
- `/software` - Software showcase (public)
- `/forms` - Forms Hub (requires login)
- `/employee-corner` - Employee Corner (coming soon)
- `/login` - Login page

## Project Structure

```
connect/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── application.html            # Original HTML file
├── templates/
│   ├── landing.html           # Landing page
│   ├── software.html          # Software page
│   ├── forms.html             # Forms Hub (requires authentication)
│   ├── login.html             # Login page
│   └── employee_corner.html   # Employee Corner (coming soon)
└── README.md                  # This file
```

## Security Notes

- Credentials are loaded from `.env` file (not hardcoded)
- Change default secret keys in production
- Use environment variables for all sensitive configuration
- `.env` file is in `.gitignore` - never commit it to version control
- In production, store credentials in a database with hashed passwords
- Implement proper SSL/HTTPS for production deployment

