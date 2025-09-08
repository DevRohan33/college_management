# College Portal

A comprehensive web-based college management system built with Django that streamlines academic operations and enhances communication between students, teachers, and administrators.

## Features

### 1. User Management
- Multi-role authentication system (Students, Teachers, HODs, Administrators)
- Profile management
- Role-based access control

### 2. Academic Management
- Course and subject management
- Assignment creation and submission
- Attendance tracking
- Results management
- Semester management
- Routine/Schedule management

### 3. Department Management
- Department-wise organization
- HOD dashboard
- Teacher management
- Student management

### 4. Student Services
- Assignment submission
- Attendance tracking
- Result viewing
- Fee management
- Course registration

### 5. Club Management
- Club creation and management
- Event organization
- Activity tracking
- Club chat system
- Real-time updates

### 6. E-Commerce Integration
- College shop management
- Product categorization
- Shopping cart functionality
- Order management
- Seller profiles

### 7. AI Integration
- Chatbot support using OpenAI
- RAG (Retrieval Augmented Generation) implementation
- Knowledge base management

### 8. Additional Features
- Real-time notifications
- Firebase integration for chat
- File upload and management
- Responsive design
- Dark mode support

## Technology Stack

- **Backend:** Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite (default), PostgreSQL (production)
- **AI Integration:** OpenAI API
- **Real-time Features:** Firebase
- **Authentication:** Django Authentication System
- **File Storage:** Django Storage
- **CSS Framework:** Bootstrap
- **Icons:** Font Awesome

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DevRohan33/college_management.git
   cd college_portal
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add:
   ```
   SECRET_KEY=your_secret_key
   EMAIL_USER=your_email
   EMAIL_PASSWORD=your_email_password
   OPENAI_API_KEY=your_openai_api_key
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

## Project Structure

```
college_portal/
├── account/            # User authentication and management
├── assignment/         # Assignment management
├── attendance/         # Attendance tracking
├── chatbot/           # AI chatbot integration
├── club/              # Club management
├── events/            # Event management
├── fees/              # Fee management
├── hod/               # HOD management
├── portal_admin/      # Admin functionality
├── result/            # Result management
├── routine/           # Class routine management
├── shop/              # E-commerce functionality
├── static/            # Static files
├── templates/         # HTML templates
└── college_portal/    # Project settings
```

## Configuration

### Environment Variables
- `SECRET_KEY`: Django secret key
- `EMAIL_USER`: Email for notifications
- `EMAIL_PASSWORD`: Email password
- `OPENAI_API_KEY`: OpenAI API key for chatbot

### Firebase Configuration
1. Create a Firebase project
2. Add Firebase configuration in `club/firebase_config.py`
3. Enable Realtime Database

## Deployment

The project is configured for deployment on Render:

1. Create a new Web Service on Render
2. Connect your repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn college_portal.wsgi:application`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email contact@example.com or create an issue in the repository.

## Acknowledgments

- Django Documentation
- OpenAI API
- Firebase Documentation
- Bootstrap Team
- Font Awesome
