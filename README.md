# EasyHire

A modern job portal built with Django that connects employers with job seekers. The platform features social authentication, job posting management, and real-time notifications.

## Features

- User Authentication (Email & Social Login)
  - Google OAuth
  - Facebook OAuth
  - GitHub OAuth
- Job Management
  - Job Posting
  - Job Applications
  - Job Alerts
- User Roles
  - Employers
  - Job Seekers
- Profile Management
- Real-time Notifications
- Responsive Design

## Tech Stack

- Django 4.2.7
- Python 3.x
- Bootstrap 5
- Font Awesome 6
- SQLite (Development)
- Django REST Framework
- Django Allauth

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/easyhire.git
   cd easyhire
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file in the project root and add your configuration:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   DEVELOPMENT=True

   # OAuth Credentials
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   FACEBOOK_APP_ID=your_facebook_app_id
   FACEBOOK_APP_SECRET=your_facebook_app_secret
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Setting up OAuth

1. Google OAuth:
   - Go to Google Cloud Console
   - Create a project
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs

2. Facebook OAuth:
   - Go to Facebook Developers
   - Create an app
   - Add Facebook Login product
   - Configure OAuth settings

3. GitHub OAuth:
   - Go to GitHub Developer Settings
   - Create a new OAuth App
   - Configure callback URL

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
