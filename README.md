# InstaCheck

InstaCheck is a Flask-based web application designed to track instagram followers based on scaning principle. Each scan records your followers and when next scan occurs it compares the previous one thus getting updated information. This README provides instructions to set up and run the application locally.

## Prerequisites

- **Python**: Version 3.10 or higher
- **MySQL**: Version 5.7 or 8.0+
- **pip**: Python package manager
- **Virtualenv**: Recommended for isolating dependencies

## Setup Instructions

### 1. Clone the Repository
Clone the project to your local machine:
```bash
git clone https://github.com/your-username/instacheck.git
cd instacheck
```

### 2. Set Up a Virtual Environment
Create and activate a virtual environment to manage dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```
Ensure `requirements.txt` includes:
- `flask`
- `sqlalchemy`
- `mysql-connector-python`
- `flask-migrate`

If `mysql-connector-python` installation fails, install MySQL development libraries:
- **Ubuntu/Debian**:
  ```bash
  sudo apt-get install libmysqlclient-dev pkg-config
  ```
- **CentOS/RHEL**:
  ```bash
  sudo yum install mysql-devel pkgconfig
  ```
- **macOS** (Homebrew):
  ```bash
  brew install mysql pkg-config
  ```

### 4. Configure the Environment
Copy the example environment file and configure it:
```bash
cp .env.example .env
```
Edit `.env` with your settings

### 5. Run database

```bash
sudo docker-compose up
```

### 6. Modify database

Initialize and apply database migrations:
```bash
flask db init  # If not already initialized
flask db migrate -m "Create users table"
flask db upgrade
```

### 7. Seed the Database
Run the seeder script to create initial data (e.g., an admin user):
```bash
python -m app.seeder
```
- Enter the admin username and password when prompted.
- Ensure the password meets MySQL's password policy (e.g., for `MEDIUM` policy: minimum 8 characters, 1 uppercase, 1 lowercase, 1 digit, 1 special character like `Secure@123`).
- If you encounter a password policy error (`ERROR 1819`), relax the policy (if you have admin privileges):
  ```sql
  SET GLOBAL validate_password.policy = LOW;
  ```

### 7. Run the Application
Start the Flask development server:
```bash
flask run
```
The app should be accessible at `http://localhost:5000`.

## Troubleshooting
- **Table 'instacheck_db.users' doesn't exist**: Ensure the database and `users` table are created (step 5). Verify the `User` model in `app/models.py`.
- **MySQL connection issues**: Check the mysql passwords in `.env` and confirm MySQL is running:
  ```bash
  sudo docker-compose up
  ```
- **Password policy issues**: Check policy settings:
  ```sql
  SHOW VARIABLES LIKE 'validate_password%';
  ```
