# Team Access Guide for Guides Project

This document outlines how team members should access and work with the project codebase, ensuring proper collaboration and security.

## Access Methods

### 1. Git Repository Access (Primary Method)

#### Setup Instructions

1. **Administrator Setup**:
   ```bash
   # Initialize repository (if new)
   git init
   
   # Add .gitignore file for Python
   curl https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore -o .gitignore
   
   # Add all files
   git add .
   
   # Initial commit
   git commit -m "Initial project structure with documentation"
   
   # Create GitHub/GitLab repository and push
   git remote add origin <repository-url>
   git push -u origin main
   ```

2. **Team Member Access**:
   ```bash
   # Clone the repository
   git clone <repository-url>
   
   # Create a virtual environment
   python -m venv venv
   
   # Activate the environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Git Workflow**:
   ```bash
   # Create a feature branch
   git checkout -b feature/your-feature-name
   
   # Make changes...
   
   # Commit changes with descriptive message
   git add .
   git commit -m "Add feature X with comprehensive comments"
   
   # Push branch to remote
   git push -u origin feature/your-feature-name
   
   # Create pull request through GitHub/GitLab interface
   ```

#### Role-Based Access Control

| Team Member | Repository Role | Access Level |
|-------------|----------------|-------------|
| Medium Level Developer | Maintainer | Read/Write access to all branches |
| Data Finder | Developer | Read/Write to data branches, Read to others |
| Cybersecurity Specialist | Developer | Read/Write to security branches, Read to others |

### 2. Local Development Environment

#### Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Redis 6+
- Node.js 18+

#### Environment Setup

1. **Database Setup**:
   ```bash
   # Create PostgreSQL database
   createdb guides_db
   
   # Create user with password
   createuser guides_user -P
   
   # Grant permissions
   psql -c "GRANT ALL PRIVILEGES ON DATABASE guides_db TO guides_user;"
   ```

2. **Environment Variables**:
   ```
   # Create a .env file in project root with:
   DJANGO_SECRET_KEY=your-secret-key
   DJANGO_DEBUG=True
   DB_NAME=guides_db
   DB_USER=guides_user
   DB_PASSWORD=your-password
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```

### 3. Docker Development Environment

For consistent development environments across the team:

```bash
# Start the development environment
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Directory Structure Access Guidelines

```
guides/
├── accounts/         # User authentication and profiles
│   └── README.md     # Component-specific documentation
├── bookings/         # Booking system
├── core/             # Core functionality
├── destinations/     # Destination management
├── docs/             # Project documentation
├── emergency/        # Emergency services
├── guides/           # Main Django project
├── itineraries/      # Itinerary planning
├── reviews/          # Review system
├── static/           # Static assets
├── templates/        # HTML templates
├── tours/            # Tour package management
└── transportation/   # Transportation management
```

### Access Responsibilities by Role

#### Medium Level Developer
- Primary responsibility: All directories
- Focus areas: `bookings/`, `itineraries/`, `core/`, `guides/`
- Documentation: Maintain API documentation, function comments in all code

#### Data Finder
- Primary responsibility: Data-related directories
- Focus areas: `destinations/`, `tours/`, `transportation/`
- Documentation: Data dictionaries, content guidelines

#### Cybersecurity Specialist
- Primary responsibility: Security-related code
- Focus areas: `accounts/`, `emergency/`, security aspects across all modules
- Documentation: Security practices, authentication flows

## Collaborative Development Guidelines

### Code Review Process
1. Create branch for new feature/fix
2. Implement with thorough documentation
3. Submit pull request
4. Code review by at least one team member
5. Address feedback
6. Merge after approval

### Documentation Requirements
- **EVERY function must have comprehensive comments**
- Document purpose, parameters, return values
- Include examples for complex functions
- Keep module-level documentation current

### Conflict Resolution
- Use Git's merge conflict resolution tools
- Discuss significant conflicts in team meetings
- Document architectural decisions

## Remote Collaboration Tools

### Communication
- Daily standups via Zoom/Teams/Meet
- Slack/Discord for quick communication
- Weekly progress reviews

### Shared Resources
- Google Drive/Dropbox for non-code documents
- Figma/InVision for design assets
- Confluence/Notion for collaborative documentation

## Security Considerations

### Access Control
- Use SSH keys for Git authentication
- Enable 2FA on GitHub/GitLab accounts
- Never share credentials via unsecured channels

### Sensitive Data
- Never commit sensitive data (.env files, keys, credentials)
- Use environment variables for secrets
- Follow the security requirements document

## Common Issues & Troubleshooting

### Git Access Issues
```bash
# SSH key issues
ssh -T git@github.com

# Permission denied errors
git remote set-url origin https://username@github.com/repo.git
```

### Environment Setup Problems
```bash
# Virtual environment issues
python -m venv --clear venv

# Database connection issues
pg_isready -h localhost
```

### Django Errors
```bash
# Migration conflicts
python manage.py showmigrations
python manage.py migrate --fake appname zero

# Static files not loading
python manage.py collectstatic --no-input
```

## Support Resources

If you encounter access issues or need help:
1. Check this guide first
2. Consult project documentation in `/docs`
3. Contact the project lead
4. Use the team communication channel for technical issues

## Access Request Process

For new team members needing access:
1. Project lead creates account on necessary systems
2. Team member generates and provides SSH public key
3. Access is granted with appropriate permissions
4. New member follows onboarding documentation
