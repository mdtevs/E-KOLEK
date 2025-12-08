# E-KOLEK - Environmental Collection System

A Django-based web application for environmental waste collection management with QR code integration, points system, and admin panel.

## Features

- **User Management**: Family-based user registration and authentication
- **QR Code System**: QR code generation and scanning for quick login
- **Points System**: Reward system for environmental activities
- **Admin Panel**: Comprehensive admin interface with role-based access
- **Mobile API**: REST API for mobile app integration
- **Google Drive Integration**: File storage using Google Drive API
- **Learning Module**: Educational content management
- **Games Module**: Gamification features
- **Security**: Advanced security features including brute force protection

## Quick Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (optional, SQLite works for development)
- Git (for version control)

### Installation

1. **Clone/Download the project**
   ```bash
   git clone <repository-url>
   cd e-kolek
   ```

2. **Run setup script**
   ```bash
   # Windows
   setup.bat
   
   # Linux/macOS
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure environment**
   - Edit `.env` file with your settings
   - Update database credentials if using PostgreSQL

4. **Create admin user**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the application**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - User Interface: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - API Documentation: http://127.0.0.1:8000/api/

## Project Structure

```
e-kolek/
├── accounts/          # User management and authentication
├── cenro/            # Main admin functionality
├── game/             # Gamification features
├── learn/            # Learning management
├── mobilelogin/      # Mobile API endpoints
├── eko/              # Project settings and configuration
├── media/            # User uploaded files
├── staticfiles/      # Static files (CSS, JS, images)
├── templates/        # HTML templates
├── requirements.txt  # Python dependencies
├── .env.example     # Environment variables template
├── setup.bat        # Windows setup script
├── setup.sh         # Linux/macOS setup script
└── TRANSFER_GUIDE.md # Detailed transfer instructions
```

## Configuration

### Environment Variables (.env)
- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: Database connection string
- `EMAIL_*`: Email configuration for notifications
- `GOOGLE_DRIVE_*`: Google Drive API settings

### Database
- Development: SQLite (default)
- Production: PostgreSQL recommended

## Admin Roles

1. **Super Administrator**: Full system access
2. **Operations Manager**: User and family management
3. **Content & Rewards Manager**: Content and rewards management
4. **Security Analyst**: Security monitoring and reports

## API Endpoints

- `/api/auth/` - Authentication endpoints
- `/api/users/` - User management
- `/api/rewards/` - Rewards system
- `/api/games/` - Game features
- `/api/learning/` - Learning content

## Security Features

- Brute force protection
- SQL injection detection
- Content Security Policy (CSP)
- Role-based access control
- Session security
- Admin activity logging

## Troubleshooting

See `TRANSFER_GUIDE.md` for detailed troubleshooting information.

## Support

For issues and questions, please check the documentation or contact the development team.

## License

This project is proprietary software. All rights reserved.
