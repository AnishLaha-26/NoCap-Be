# NoCap Backend

Django REST Framework backend for the NoCap application.

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NoCap-Be
   ```

2. **Create and activate virtual environment**
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows
   # python -m venv venv
   # .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Update the environment variables in `.env` as needed

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
NoCap-Be/
├── backend/               # Main project directory
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py       # Project settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py
├── manage.py            # Django management script
├── requirements.txt     # Project dependencies
└── .env                 # Environment variables (not in version control)
```

## API Documentation

Once the development server is running, you can access:

- API Root: http://localhost:8000/api/
- Admin Interface: http://localhost:8000/admin/
- DRF Browsable API: http://localhost:8000/

## Development

- Always activate the virtual environment before working on the project
- Install new dependencies with `pip install <package>` and update `requirements.txt` with `pip freeze > requirements.txt`
- Follow PEP 8 style guide for Python code
- Write docstrings for all functions and classes

## Deployment

For production deployment, make sure to:
1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Configure proper database settings
4. Set up a production web server (e.g., Gunicorn with Nginx)
5. Configure proper CORS settings

## License

[Specify your license here]
