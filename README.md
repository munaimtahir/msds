# AdminOS Lab

This repository contains the AdminOS Lab Django project. The project includes a
set of registers with accompanying tests that ensure the core functionality of
the application remains stable.

## Local development and testing

Follow the steps below to mirror the checks executed in continuous integration
and to run the test suite locally:

1. **Create and activate a virtual environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python dependencies** using the provided requirements file:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. **Apply database migrations** so the Django schema is up to date before
   running tests:
   ```bash
   python manage.py migrate --noinput
   ```

4. **Run the automated test suite** with `pytest`:
   ```bash
   pytest
   ```

The commands above match the steps configured in the GitHub Actions workflow,
allowing you to reproduce the CI environment locally.
