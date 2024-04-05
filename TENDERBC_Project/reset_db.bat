echo Removing db.sqlite3
del db.sqlite3

echo Moving to TENDERBC_App
cd TENDERBC_App

echo Removing migrations
rmdir /s /q migrations

echo Creating migrations folder
mkdir migrations

echo Moving to migrations
cd migrations

echo Creating __init__.py
echo. > __init__.py

echo Moving to TENDERBC_App
cd ..

echo Moving to TENDERBC_Project
cd ..

echo Making Migrations
python manage.py makemigrations

echo Migrating
python manage.py migrate

echo Creating Superuser
python manage.py createsuperuser --username admin --email admin@gmail.com



