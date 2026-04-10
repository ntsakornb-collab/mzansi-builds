# MzansiBuilds

A Flask-based "build in public" community platform where users can share projects, get support, leave comments, and celebrate completed work.

## Architecture

- **Backend**: Python / Flask (port 5000)
- **Database**: SQLite (`app.db`)
- **Templates**: Jinja2 (in `templates/` directory)

## Features

- User registration and login (password hashed with SHA-256)
- Create projects with title, description, stage, and support type
- Live feed of all projects
- Individual project pages with comments
- "Raise Hand" for collaboration on any project
- Update project stage (planning / in_progress / completed)
- Celebration Wall showing all completed projects

## Database Schema

- **users**: id, name, email, password
- **projects**: id, user_id, title, description, stage, support
- **comments**: id, project_id, user_id, comment, date

## Running

The app runs via the "Start application" workflow using `python main.py` on port 5000.

## Files

- `main.py` — Flask app with all routes
- `templates/` — Jinja2 HTML templates
  - `base.html` — shared layout and nav
  - `index.html`, `register.html`, `login.html`
  - `feed.html`, `new.html`, `project.html`, `wall.html`
