# Curiosite Backend

Backend API for **Curiosite**, an online learning platform where instructors publish courses and posts, students enroll, track progress, earn certificates, subscribe to plans, and chat with each other and with an AI tutor.

Built with Django REST Framework, JWT authentication, WebSockets (Django Channels), Redis, PostgreSQL, and object storage (S3-compatible).

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language / Runtime | Python 3.12 |
| Framework | Django 5.2, Django REST Framework 3.17 |
| Auth | `djangorestframework-simplejwt` (access + refresh tokens, blacklist) |
| Realtime | Django Channels 4 + Daphne, `channels_redis` |
| Database | PostgreSQL (`psycopg2`) |
| Cache / Channel layer | Redis (`django-redis`) |
| File storage | Local media in dev, S3-compatible storage (`django-storages`, `boto3`) in production |
| Static files | WhiteNoise |
| Email | Resend |
| AI | Google Gemini (`google-genai`) for lesson Q&A and audio generation |
| Certificates | PDF generation (`weasyprint` / `reportlab`) |
| Server | Gunicorn (Procfile) |

---

## Features

- **Authentication & accounts** — signup with email or phone, verification codes, account activation, login/logout, password change and reset, token refresh, account deletion, role upgrade to instructor.
- **Profiles** — student and instructor profiles, avatars with automatic thumbnails, interests, friend requests and friendships, instructor approval workflow.
- **Courses** — categories, tags, courses (draft → in review → published), modules and lessons (video, article, quiz, assignment), filtering, instructor feeds.
- **Enrollments** — enroll/drop, per-lesson progress, progress percentage, last-accessed lesson, course completion.
- **Payments** — student wallet, wallet top-up, subscription plans, course purchases, subscriptions with expiry.
- **Quizzes** — quizzes attached to lessons, questions (radio/checkbox/text), options, attempts and scoring.
- **Reviews** — one review per student per course, course rating aggregation.
- **Posts** — instructor blog posts with cover images, likes, comments, feeds and reading time.
- **Chat** — 1:1 and course group conversations, WebSocket messaging, attachments, replies, forwarding, typing indicators, presence, read receipts, unread tracking, rate limiting.
- **Notifications** — per-user notifications with types and read state.
- **Certificates** — generated PDF certificates for completed courses; public lookup by certificate ID.
- **Leaderboard** — student ranking by XP plus personal placement.
- **AI tutor** — Gemini-powered lesson Q&A (`interaction_id` for multi-turn chat) and text-to-speech audio.
- **Admin API** — dashboard stats and management of instructors, students, courses, lessons, enrollments, posts, wallets, and notifications.
- **Django admin** at a custom (non-default) URL.

---

## Project Structure

```
backend/
├── core/            # Settings, root URL config, ASGI/WSGI entrypoints
├── baseapp/         # Shared BaseModel (UUID pk, timestamps), pagination, permissions, helpers
├── authentication/  # CustomUser, verification codes, JWT auth, account lifecycle
├── profiles/        # Student/instructor profiles, friendships, interest tags
├── courses/         # Categories, tags, courses, modules, lessons
├── enrollments/     # Enrollment, lesson progress, completion signals
├── payments/        # Wallet, transactions, plans, subscriptions, purchases
├── quizzes/         # Quizzes, questions, options, attempts
├── reviews/         # Course reviews and rating aggregation
├── posts/           # Instructor posts, likes, comments
├── chat/            # Conversations, messages, REST API + WebSocket consumer
├── notifications/   # User notifications
├── certificates/    # Certificate records and PDF generation
├── leaders/         # Leaderboard and XP ranking
├── management/      # Admin-facing API
├── integration/     # Gemini AI text/audio endpoints
├── templates/       # Templates used for generated PDFs (e.g. certificates)
├── static/          # Development static assets
├── staticfiles/     # collectstatic output
├── manage.py
├── Procfile
└── requirements.txt
```

All models inherit from `baseapp.models.BaseModel`, which provides a UUID primary key and `created_at` / `updated_at` fields.

---

## Getting Started

### Prerequisites

- Python 3.12
- PostgreSQL
- Redis (required for Channels and caching)
- FFmpeg is **not** required; audio is generated via the Gemini API.

### 1. Clone and create a virtual environment

```bash
git clone <repository-url>
cd backend
python -m venv venv
```

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root (next to `manage.py`):

```env
# Django
SECRET_KEY=change-me
DEBUG=True

# PostgreSQL
PGDATABASE=curiosite
PGUSER=postgres
PGPASSWORD=your-password
PGHOST=127.0.0.1
PGPORT=5432

# Redis (channels + cache)
REDIS_URL=redis://127.0.0.1:6379

# Email (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxx
EMAIL_HOST_USER=noreply@example.com

# Frontend (used for password-reset links and CORS)
FRONTEND_URL=http://localhost:5173

# AI
GEMINI_API_KEY=your-gemini-key

# Object storage (production only; required when DEBUG is not True)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET_NAME=
AWS_ENDPOINT_URL=
AWS_DEFAULT_REGION=auto
```

> When `DEBUG` is `False`, the project automatically enables S3-compatible storage via `django-storages`, so the `AWS_*` variables must be set in production.

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create an admin user (optional)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

Because the project uses Django Channels, run it through Daphne (or `runserver`, which is provided by `daphne` in `INSTALLED_APPS`):

```bash
python manage.py runserver
```

Redis must be running for WebSocket features and caching.

API root: `http://127.0.0.1:8000/api/`
Admin: `http://127.0.0.1:8000/admin-secure-code4303/`

---

## Authentication

The API uses **JWT bearer tokens**.

1. `POST /api/auth/signup` — register with email or phone.
2. `POST /api/auth/verification-code` — send a verification code.
3. `POST /api/auth/activation` — activate the account with the code.
4. `POST /api/auth/login` — obtain `access` and `refresh` tokens.

Send the access token on protected endpoints:

```
Authorization: Bearer <access_token>
```

Access tokens live 30 minutes, refresh tokens 5 days. Refresh via `POST /api/auth/token-refresh`.

WebSocket connections authenticate with the **access token as a query parameter**:

```
ws://127.0.0.1:8000/ws/chat/<conversation_id>/?token=<access_token>
```

### Response envelope

Most endpoints return a consistent shape:

```json
{
  "success": true,
  "message": "Response",
  "data": { }
}
```

Errors:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": { "field": "message" }
}
```

---

## API Reference

All routes are prefixed with `/api/`. `<uuid>` and `<slug>` denote path parameters.

### Auth — `/api/auth/`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `signup` | Register with email or phone |
| POST | `verification-code` | Send verification code |
| POST | `activation` | Activate account with code |
| POST | `login` | Obtain JWT tokens |
| POST | `logout` | Blacklist refresh token |
| POST | `token-refresh` | Refresh access token |
| GET/PATCH | `my-profile` | Current user profile |
| PATCH | `update-profile` | Update account details |
| GET | `profile-info/<uuid>` | Public profile info |
| POST | `password-change` | Change password |
| POST | `password-reset-request` | Request password reset email |
| POST | `password-reset-confirm` | Confirm password reset |
| DELETE | `delete-account` | Delete own account |
| POST | `veirfy-email` / `veirfy-phone` | Verify email / phone |
| PATCH | `preference` | Theme, language, notification prefs |
| GET | `search-users` | Search users |
| POST | `become-instructor` | Request instructor role |

> Note: the verification endpoints are spelled `veirfy-email` and `veirfy-phone` in the current codebase.

### Profiles — `/api/profile/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET/PATCH | `student-profile` | Own student profile |
| GET/PATCH | `instructor-profile` | Own instructor profile |
| GET | `get-student-profile/<uuid>` | Public student profile |
| GET | `get-instructor-profile/<uuid>` | Public instructor profile |
| POST | `send-request` | Send friend request |
| POST | `accept-request/<uuid>` / `reject-request/<uuid>` / `cancel-request/<uuid>` | Manage friend requests |
| GET | `my-requests` / `incoming-requests` | Sent / received requests |
| GET | `friends/<uuid>` | Friend list |
| DELETE | `remove-friendship/<uuid>` | Remove a friend |

### Courses — `/api/courses/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET/POST | `categories`, `categories/<uuid>` | List/create and manage categories |
| GET/POST | `tags`, `tags/<uuid>` | Tags |
| GET | `instructors` | Instructor directory |
| GET/POST | `course-create` | Create a course |
| PATCH/DELETE | `course-update-delete/<uuid>` | Update/delete course |
| GET | `course-detail/<slug>` | Course details |
| POST | `send-to-review/<uuid>` | Submit course for review |
| GET | `my-feed` | Personalized course feed |
| GET | `filtered-courses`, `instructor-courses` | Filtering |
| GET | `complete-course/<uuid>` | Course completion data |
| CRUD | `module-create`, `module-update-delete/<uuid>`, `module-detail/<uuid>` | Modules |
| CRUD | `lesson-create`, `lesson-update-delete/<uuid>`, `lesson-detail/<uuid>`, `lesson-curriculum/<uuid>` | Lessons |

### Enrollments — `/api/enrollments/`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `enrollment-create` | Enroll in a course |
| POST | `enrollment-drop/<uuid>` | Drop a course |
| GET | `my-enrollments` | Current user's enrollments |
| POST | `lesson-progress/<uuid>` | Mark lesson complete |
| GET | `last-lesson` | Resume last accessed lesson |

### Payments — `/api/payments/`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `replenish-wallet` | Top up wallet |
| GET | `plans` | Available subscription plans |
| POST | `subscribe` | Subscribe to a plan |
| POST | `buy-course` | Purchase a course |
| GET | `my-wallet` | Wallet balance and transactions |
| GET | `my-subscriptions` | Active subscriptions |

### Quizzes — `/api/quizzes/`

| Method | Endpoint | Description |
| --- | --- | --- |
| CRUD | `create-quiz`, `update-delete-quiz/<uuid>`, `get-quiz/<uuid>` | Quizzes |
| CRUD | `create-question`, `delete-question/<uuid>` | Questions |
| CRUD | `create-option`, `delete-option/<uuid>` | Options |
| POST | `quiz-attempt/<uuid>` | Submit a quiz attempt |

### Reviews — `/api/reviews/`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `review-create` | Create a review |
| PATCH/DELETE | `review-update-delete/<uuid>` | Update/delete own review |
| GET | `course/<uuid>` | Reviews for a course |
| GET | `my-reviews` | Own reviews |
| GET | `is-reviewed/<uuid>` | Whether the user reviewed a course |

### Posts — `/api/posts/`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `create-post` | Create a post |
| GET | `post-detail/<slug>` | Post details |
| POST | `post-image-upload` | Upload inline image |
| PATCH/DELETE | `post-update-delete/<uuid>` | Update/delete post |
| GET | `filtered-posts`, `feed-posts`, `instructor-posts/<uuid>` | Feeds |
| POST | `like-post/<uuid>` | Toggle like |
| POST | `comment-post/<uuid>` | Add comment |
| PATCH/DELETE | `comment-update-delete/<uuid>` | Manage comment |
| GET | `my-likes`, `my-comments` | Own activity |

### Chat — `/api/chat/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET/POST | `/` | List conversations / create one |
| GET/DELETE | `<conversation_id>/` | Conversation details |
| GET | `<conversation_id>/messages/` | Message history |
| PATCH/DELETE | `messages/<message_id>/` | Edit/delete message |
| POST | `conversations/<conversation_id>/messages/upload/` | Upload attachment |
| POST | `conversations/<conversation_id>/messages/forward/` | Forward messages |
| POST | `join-course-group/` | Join a course group conversation |
| POST | `connect-ticket/` | Obtain a short-lived ticket for the socket |

### Notifications — `/api/notifications/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `my-notifications` | List notifications |
| PATCH/DELETE | `read-delete-notification/<uuid>` | Mark read / delete |

### Certificates — `/api/certificates/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `my-certificates` | Certificates earned by the user |
| GET | `student-certificate/<uuid>` | Public certificate lookup |

### Leaderboard — `/api/leaderboard/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `leaders` | Ranked students |
| GET | `my-place` | Current user's rank |

### AI — `/api/ai/`

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `ask-ai/<lesson_uuid>?prompt=...&interaction_id=...` | Ask the AI tutor about a lesson |
| POST | `get-audio` | Convert text to speech (`text_input`) |

### Admin — `/api/admin/`

Requires an admin/superuser account.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `dashboard/` | Platform statistics |
| GET | `instructors/`, `instructors/<uuid>/` | List / inspect instructors |
| POST | `instructors/<uuid>/approval/` | Approve or reject an instructor |
| GET | `students/`, `students/<uuid>/` | List / inspect students |
| GET | `courses/`, `courses/<uuid>/` | List / inspect courses |
| POST | `courses/<uuid>/status/` | Change course status |
| GET | `lessons/<uuid>/` | Lesson details |
| GET | `enrollments/` | Enrollment list |
| GET | `posts/` | Post list |
| POST | `wallet-topup/` | Credit a student wallet |
| POST | `notifications/send/` | Broadcast a notification |

---

## WebSocket Chat

Endpoint:

```
ws://<host>/ws/chat/<conversation_id>/?token=<access_token>
```

The connection is accepted only for authenticated participants of the conversation. Close codes:

| Code | Meaning |
| --- | --- |
| 4001 | Not authenticated |
| 4003 | Not a participant |
| 4004 | Conversation not found |

Message types (JSON `type` field):

| Type | Direction | Purpose |
| --- | --- | --- |
| `message` (default) | client → server | Send a chat message |
| `typing` | both | Typing indicator (`is_typing`) |
| `read` | client → server | Mark messages read up to `message_id` |
| `ping` | client → server | Keep-alive, server replies `pong` |
| `chat_message`, `typing_event`, `presence_event`, `read_event`, `chat_message_edit`, `chat_message_delete`, `conversation_deleted`, `error` | server → client | Server events |

Messages are rate-limited to 100 per 100 seconds per connection.

---

## Deployment

The included `Procfile` runs migrations and serves the ASGI app with Gunicorn:

```
python manage.py migrate && web: gunicorn core.wsgi --bind 0.0.0.0:8080 --access-logfile - --error-logfile -
```

For full WebSocket support in production, serve `core.asgi:application` with an ASGI server (e.g. Daphne or Uvicorn) behind a reverse proxy, and ensure a shared Redis instance is available for the channel layer.

Production checklist:

1. Set `DEBUG=False` and a strong `SECRET_KEY`.
2. Point `PG*` variables at the production database.
3. Provide `REDIS_URL`.
4. Configure S3-compatible storage variables (`AWS_*`).
5. Run `python manage.py collectstatic` (WhiteNoise serves the files).
6. Update `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` in `core/settings.py` for your domain.

---

## Notes

- Timezone is `Asia/Tashkent`; all stored datetimes are timezone-aware.
- Email and phone verification codes expire after 5 minutes (`EMAIL_EXPIRATION_TIME`, `PHONE_EXPIRATION_TIME`).
- Images (avatars, course thumbnails, post covers) are automatically resized/optimized on save.
- Slugs for courses, categories, and posts are generated automatically and de-duplicated.
