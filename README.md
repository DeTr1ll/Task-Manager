```
+-------------------------------------------------------------------------+
|                 _______           _     _                               |
|                |__   __|         | |   (_)                              |
|                   | |  __ _  ___ | | __ _  _ __    ___                  |
|                   | | / _` |/ __|| |/ /| || '_ \  / _ \                 |
|                   | || (_| |\__ \|   < | || | | || (_) |                |
|                   |_| \__,_||___/|_|\_\|_||_| |_| \___/                 |
| _______           _      __  __                                         |
||__   __|         | |    |  \/  |                                        |
|   | |  __ _  ___ | | __ | \  / |  __ _  _ __    __ _   __ _   ___  _ __ |
|   | | / _` |/ __|| |/ / | |\/| | / _` || '_ \  / _` | / _` | / _ \| '__||
|   | || (_| |\__ \|   <  | |  | || (_| || | | || (_| || (_| ||  __/| |   |
|   |_| \__,_||___/|_|\_\ |_|  |_| \__,_||_| |_| \__,_| \__, | \___||_|   |
|                                                        __/ |            |
|                                                       |___/             |
+-------------------------------------------------------------------------+
```


A simple **Task Manager** built with **Django** and **Django REST Framework**.  
It allows users to create, manage, and organize their tasks with tags, deadlines, and filters.

---

## Features

- User authentication and personal account
- Create, edit, and delete tasks
- Task deadlines with visual highlighting:
  - Yellow for upcoming deadlines
  - Red for overdue tasks
- Tag system:
  - Add multiple tags separated by commas
  - Autocomplete suggestions while typing
- Search and filtering:
  - Search tasks by title or tags
  - Sort tasks by deadline
  - Completed tasks are displayed at the bottom
- Responsive UI with a modern design
- API support (JWT authentication)

---

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL (via `dj-database-url`)
- **Frontend**: Django templates, Bootstrap, Flatpickr (for date/time pickers)
- **Authentication**: JWT (SimpleJWT)
- **Deployment**: Gunicorn + Render

---

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/taskmanager.git
   cd taskmanager
   ```
2.  Create and activate a virtual environment:
  ```
  python -m venv venv
  source venv/bin/activate   # Linux/Mac
  venv\Scripts\activate      # Windows
  ```
3. Install dependencies:
  ```
  pip install -r requirements.txt
  ```
4. Set up the environment variables in a .env file:
  ```
  SECRET_KEY=your_secret_key
  DEBUG=True
  DATABASE_URL=postgres://user:password@localhost:5432/taskmanager
  ```
5. Apply migrations:
  ```
  python manage.py migrate
  ```
6. Create a superuser:
  ```
  python manage.py createsuperuser
  ```
7. Run the development server:
  ```
  python manage.py runserver
  ```
8. Running Tests
  ```
  python manage.py test
  ```
