## Installation

### Python and PostgreSQL

Create python virtual environment and activate </br>
Install all requirements from `requirements.txt`

```
python3 -m venv venv
source ./venv/bin/activate

pip install -r requirements.txt
```

Install PostgreSQL for the database

```
apt install postgresql
```

Create a database with name `pbxteensclub_db`

```
createdb -U postgres pbxteensclub_db
```

### Environment Variable

This is the `.env` template that you can use. </br>
Replace the parts enclosed in angle brackets `<>` (the brackets too) with your own data.

```env
DATABASE_URL="postgresql+psycopg://postgres:<password>@<ip>:<port>/pbxteensclub_db"
```