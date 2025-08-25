# College Portal (Django)

A full-featured college management portal built with Django. It supports multiple roles (Admin, Management, HOD, Teacher, Student), academic modules (Subjects, Class Routines, Attendance, Assignments, Results), community modules (Clubs with chat and polls), and a campus marketplace (Shop with orders, reviews, and seller profiles). Real-time features leverage Django Channels.


## Contents
- Overview
- Features by Role and Module
- Architecture and Tech Stack
- Local Development Setup
- Initial Data Seeding (Recommended)
- Running the App (HTTP + WebSocket)
- Deployment (Render.com)
- URL Map (Key Routes)
- Data Model Overview
- Templates, Static, Media
- Security and Configuration
- Known Issues / TODO
- Contributing


## Overview
This portal centralizes day-to-day college operations:
- Authentication with role-based dashboards.
- Department and semester-aware content (subjects, routines, attendance, assignments, results).
- Teacher utilities: attendance, grading, student listings.
- Student utilities: attendance analytics, assignments, results, clubs, shop.
- Community: Clubs (join, manage, chat, polls, events, activities) with WebSockets.
- Marketplace: Buy/sell items within campus; orders, reviews, seller payment details.


## Features by Role and Module

### Roles
- Admin
- Management
- Head of Department (HOD)
- Teacher
- Student

### Account and Auth
- Custom user model (account.User) with role, department, semester, and teacher-accessible batches.
- Dashboards per role with summarized metrics and quick links.
- Login/Logout, Change Password, and password reset via email OTP flow.
- Context processors provide commonly used data in templates (teacher profile, shop counters).

Key screens:
- Public landing: /
- Login: /login/
- Role dashboards:
  - Admin: /admin-dashboard/
  - Management: /management-dashboard/
  - HOD: /hod-dashboard/
  - Teacher: /teacher-dashboard/
  - Student: /student-dashboard/

### Departments, Semesters, Subjects, Routines
- Department and Semester models define academic structure.
- Subjects are bound to Department and Semester; multiple teachers can be assigned to a subject.
- ClassRoutine ties Department + Semester + Day + Time + Subject + Teacher.
- HOD creates/edits class routines; teachers view their own.

Key screens:
- Routine (HOD create/edit): /routine/classes/create/, /routine/classes/<id>/edit/
- Teacher schedule: /routine/teacher/my-classes/

### Attendance (Teacher + Student)
- Teachers can take attendance for classes assigned via routine or via direct subject assignment.
- Enforced single attendance per date per class; custom attendance for non-scheduled sessions.
- History per subject/semester with per-session stats.
- Export per-session Excel-compatible HTML and time-range reports.
- Students view detailed analytics: overall %, per-subject stats, daily timeline chart data.

Key screens (prefix path is /attendence):
- Teacher: take/select: /attendence/attendance
- Teacher: mark today: /attendence/attendance/<subject_id>/<semester_id>/
- Teacher: custom session: /attendence/attendance/custom/
- Teacher: history: /attendence/attendance/history
- Teacher: subject history: /attendence/attendance/history/<subject_id>/<semester_id>/
- Teacher: detail: /attendence/attendance/detail/<attendance_id>/
- Export session: /attendence/attendance/export/session/<attendance_id>/
- Export report: /attendence/attendance/export/?period=weekly|monthly|custom&start=YYYY-MM-DD&end=YYYY-MM-DD&download=1
- Student: /attendence/attendance/

Notes:
- Routes use the root prefix "attendence" (typo), which is correct per configuration.

### Assignments
- Teachers/HOD create assignments bound to subject, department, semester with a submission deadline.
- Students see assignments for their department/semester, upload a single file per assignment; duplicate submission prevention.
- Teacher detail view shows submitted vs due students with counts.

Key screens (prefix path is /assignment):
- Create: /assignment/new_assignments/
- All assignments (teacher list): /assignment/all_assignments/
- Detail (teacher): /assignment/assignments/<pk>/
- Student list: /assignment/my_assignments/
- Student submit: /assignment/submit_assignment/<assignment_id>/

### Results / Grading
- Exam sessions per subject/semester/department for CA1–CA4 (theory subjects).
- Teachers enter marks; teacher/HOD can lock sessions to prevent further edits.
- Student results page shows CA table by subject for selected semester.
- SGPA tracker: students can record SGPA by semester; overall average and percent-like metric displayed.

Key screens (prefix path is /result):
- Teacher grade dashboard: /result/teacher/grades/
- Grade entry: /result/teacher/grades/entry/<subject_id>/<semester_id>/<exam_type>/
- Lock session: /result/teacher/grades/lock/<session_id>/
- Student results: /result/student/results/

### Student Profile
- Edit profile, including profile image and personal details.
- Auto-created student profile on user creation (role=student).

Key screen:
- /student/edit/

### Teacher Area
- Teacher profile with education, primary subject, abilities, bio.
- Students list by semester in teacher’s department; detail view includes attendance entries.

Key screens (prefix path is /teacher):
- Profile: /teacher/profile/
- Students: /teacher/students/
- Student detail: /teacher/students/<user_id>/

### HOD Area
- Teachers list in department, teacher detail page showing today’s classes, notices.
- Edit teacher basic info (via form).

Key screens (prefix path is /hod):
- Teacher list: /hod/teachers/
- Teacher detail: /hod/teachers/<pk>/
- Edit teacher: /hod/teachers/<pk>/edit/

### Portal Admin (User Management)
- Management role (or superuser) can list, create, edit, delete users via web forms.

Key screens (prefix path is /portal_admin):
- Users: /portal_admin/users/
- Add user: /portal_admin/users/add/
- Edit user: /portal_admin/users/<pk>/edit/
- Delete user: /portal_admin/users/<pk>/delete/

### Events / Notices
- Create and list notices; created_by set automatically, department stored as name string.

Key screens (prefix path is /event):
- List: /event/
- Create: /event/creat/

### Clubs (Community)
- Clubs with unique invite codes.
- Join requests with approval moderation. Roles: owner, admin, moderator, member; statuses: pending, active, banned; badges and points for ranking.
- Real-time chat per club (WebSocket), polls (create and vote), emoji reactions on messages, member online status, activities feed and events.

Key screens (prefix path is /clubs/):
- List: /clubs/
- Create: /clubs/create/
- Detail: /clubs/<unique_id>/
- Manage members: /clubs/<unique_id>/manage/
- Approve/Reject/Remove: /clubs/<unique_id>/approve|reject|remove/<member_id>/
- Chat: /clubs/<unique_id>/chat/
- Polls: /clubs/<unique_id>/chat/poll/create (POST), /clubs/<unique_id>/chat/poll/vote (POST)
- Online members: /clubs/<unique_id>/chat/online/
- Reactions: /clubs/<unique_id>/chat/react/ (POST)
- Activities: /clubs/<unique_id>/activities/
- Events: /clubs/<unique_id>/events/

WebSocket:
- Path: ws/club/<unique_id>/ (served via Channels ASGI routing)

### Shop (Campus Marketplace)
- Products with multiple images, categories, ratings; seller average ratings aggregated from reviews.
- Cart, Buy Now flow, Orders with statuses (REQUESTED, DELIVERY_DAY, DELIVERED, CANCELLED), payment method (ONLINE/COD), payment screenshot upload.
- Sellers manage products, orders, delivery dates; store UPI and QR code.
- Reviews allowed post-delivery; one review per buyer per product.

Key screens (prefix path is /shop/):
- Home with filters and search: /shop/
- Product detail: /shop/product/<pk>/
- Cart: /shop/cart/
- Buy now: /shop/buy/<pk>/
- My orders: /shop/orders/
- Add review: /shop/orders/<order_id>/review/
- My shop (seller dashboard): /shop/my/
- Add product: /shop/my/add/
- Manage product: /shop/my/product/<pk>/
- Delete product: /shop/my/product/<pk>/delete/
- Cancel order (seller): /shop/my/order/<order_id>/cancel/


## Architecture and Tech Stack
- Django 5.2.5
- Custom user model: account.User with fields: role, department(FK), semester(FK), accessible_batches(M2M for teachers)
- Django apps: account, attendance, result, fees, events, subject, routine, student, hod, portal_admin, assignment, club, teacher, shop
- Templates from a shared /templates directory with per-app folders
- Channels (ASGI) for WebSockets, channel layer configured for Redis
- Database: SQLite (default); can be swapped for Postgres/MySQL
- Static files: /static -> collected to /staticfiles for prod
- Media uploads: /media
- Context processors:
  - account.context_processors.profile_context (injects teacher profile)
  - shop.context_processors.shop_counts (cart count, seller pending orders)


## Local Development Setup
Requirements:
- Python 3.10+
- Redis (for Channels WebSocket layer) running locally if you use the club chat in dev
- Git, pip

Steps:
1) Clone and enter the project
   git clone <your-repo-url>
   cd college_portal

2) Create and activate a virtualenv
   python -m venv venv
   venv\Scripts\activate   # Windows
   # or: source venv/bin/activate

3) Install dependencies
   pip install -r requirements.txt

   If requirements.txt is missing, install minimums:
   pip install "Django==5.2.5" channels channels-redis pillow django-widget-tweaks

4) Environment configuration
   - Copy .env.example to .env (if present) and set values; otherwise set environment variables:
     - DJANGO_SETTINGS_MODULE=college_portal.settings
     - SECRET_KEY=<your-secret>
     - DEBUG=True
     - EMAIL_* settings (use app password for Gmail if using Gmail SMTP)
     - CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

   Also review college_portal/settings.py and move secrets out of source control before production.

5) Database setup
   python manage.py migrate
   python manage.py createsuperuser

6) Static and media (dev)
   - Static files are served from /static; media from /media in DEBUG mode.

7) Run development server
   python manage.py runserver

8) (Optional) Run Redis for WebSockets (club chat)
   - Ensure a Redis instance is running at 127.0.0.1:6379.
   - CHANNEL_LAYERS is configured to use channels_redis; see settings.py.


## Initial Data Seeding (Recommended)
Create baseline data via admin site (/admin/) or the provided UIs.
- Departments (e.g., CSE, ECE, IT)
- Semesters for each department (1..8)
- Subjects per department + semester; assign teachers (M2M)
- Users for each role (Admin, Management, HOD, Teacher, Student)
  - For Teachers: set department and add accessible_batches (semesters they handle)
  - For Students: set department and semester
- Class routines per department/semester
- Categories (for shop)


## Running the App (HTTP + WebSocket)
- HTTP: Django dev server via manage.py runserver is sufficient in development.
- WebSocket: ASGI is configured in asgi.py, and Channels routes WebSocket traffic to the club app routes.
- In production, prefer daphne/uvicorn with Redis for Channel layers.

WebSocket route:
- ws/club/<unique_id>/

ASGI application entrypoint:
- college_portal/asgi.py


## Deployment (Render.com)
A render.yaml is provided (services.college-portal) which:
- Installs requirements, runs migrate, collectstatic
- Starts server with python manage.py runserver 0.0.0.0:$PORT

Notes:
- For Channels in production, prefer daphne rather than runserver. Example:
  startCommand: daphne -b 0.0.0.0 -p $PORT college_portal.asgi:application
- Add REDIS_URL and configure CHANNEL_LAYERS accordingly to point to your Redis instance.
- Set proper environment variables: DJANGO_SETTINGS_MODULE, SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, EMAIL_*.


## URL Map (Key Routes)
Root router: college_portal/urls.py
- Admin: /admin/
- Account (root): '' (index, login, dashboards, events list)
- Student: /student
- Events: /event
- Routine: /routine
- Teacher: /teacher
- HOD: /hod
- Portal Admin: /portal_admin
- Attendance: /attendence
- Assignment: /assignment
- Clubs: /clubs/
- Result: /result
- Shop: /shop/

See each app's urls.py for detailed endpoints (summarized in Features above).


## Data Model Overview (selected)
- account.Department(name)
- account.Semester(department FK, semester int, unique per department)
- account.User(AbstractUser): role, department FK, semester FK, accessible_batches M2M->Semester
- subject.Subject: name, code, subject_type (theory/practical), department FK, semester FK, teachers M2M->User
- routine.ClassRoutine: department FK, semester FK, day_of_week, times, subject FK, teacher FK
- attendance.Attendance: department FK, semester FK, subject FK, date, taken_at
- attendance.AttendanceEntry: attendance FK, student FK(User), status
- assignment.Assignment: title, details, subject FK, department FK, semester FK, created_by FK(User), submit_last_date
- assignment.AssignmentSubmission: assignment FK, student FK(Student profile), file, submitted_at
- result.ExamSession: department FK, semester FK, subject FK, exam_type (CA1..CA4), full_marks, created_by, lock fields
- result.ExamMark: session FK, student FK(User), marks
- result.StudentSGPA: student FK(User), semester_num, sgpa
- student.Student: OneToOne to User with profile details
- teacher.TeacherProfile: OneToOne to User with profile details
- events.Notice: title, description, created_by FK(User), department (string)
- club.Club, ClubMember, ClubChat, PollOption, PollVote, ClubActivity, ClubEvent, ClubChatReaction
- shop.Category, Product (+images), ProductReview, CartItem, Order, SellerProfile


## Templates, Static, Media
- Templates located in /templates with subfolders per app: dashboards/, student_profiles/, teacher/, club/, shop/, event/, hod/, admin/, result/
- Base templates: base.html, login-base.html, student_base.html, teacher_base.html, club_base.html
- Static configured via STATICFILES_DIRS for dev and STATIC_ROOT for collectstatic
- Media uploads stored under /media; ensure MEDIA_ROOT exists and is writable

Context processors add:
- profile (teacher profile) when authenticated
- shop_count metrics (cart_count, seller_pending_count, shop_total_count)


## Security and Configuration
- Move secrets to environment variables: SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEBUG, ALLOWED_HOSTS
- Set CSRF_TRUSTED_ORIGINS to your domains
- Use app-specific password for Gmail or use a transactional email provider
- Enforce HTTPS and secure cookies in production
- Configure Redis for Channels in production

Email (settings.py):
- EMAIL_BACKEND=smtp
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587, EMAIL_USE_TLS=True
- EMAIL_HOST_USER, EMAIL_HOST_PASSWORD required


## Known Issues / TODO
- WebSocket consumer name mismatch: club/routing.py references consumers.ChatConsumer but consumers.py defines ClubChatConsumer. Update routing or class name so they match to enable live chat.
- Attendance root path spelling: the project uses "/attendence" as base prefix (with an extra ‘e’). Keep routes as-is or standardize across code and templates if you plan to rename.
- Events.Notice.department is a CharField storing department name string, while most of the app uses FK to Department. Consider migrating to a ForeignKey for consistency.
- Settings currently include inline secrets. Extract to environment variables before deploying.
- Requirements file: if missing, add a requirements.txt with pinned versions.
- Production ASGI: switch to daphne/uvicorn and configure Redis URL in CHANNEL_LAYERS.


## Contributing
- Use feature branches; open PRs for review.
- Keep migrations consistent; run makemigrations/migrate as you modify models.
- Follow Django best practices: use the custom user model (account.User) in all auth references.
- Maintain consistency of department/semester logic when adding new modules.


## Quick Start Commands
- Migrate: python manage.py migrate
- Create superuser: python manage.py createsuperuser
- Run dev server: python manage.py runserver
- Collect static (prod): python manage.py collectstatic --noinput


## License
Internal project. Add a LICENSE file if you plan to open-source.
