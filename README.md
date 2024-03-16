# DojicsEvaluationTask
This repository is about assessment which is an Evaluation Task. The Repository contains couple of backend which Django and Fast api
There is a Django Restframework api for user registration and authentication. The api is utilizing built in token authentication. Swagger documentation is also integrated with it. Fastapi has been used to for taskmanagement.

### Dependancy
You will need to include you smtp email server credentials in the function `send_email_notiifcation` in app.py file. Without these you will not be able to use task management api.

### Setup
1. Clone the repository
```
git clone <repository_url>
cd <project_directory>
```
2. Create a virtual environment (optional but recommended):

```
python3 -m venv env
source env/bin/activate
```
3. Install dependencies:
```
pip install -r requirements.txt
``` 
4. Migrate the database:
```
python manage.py migrate
```
5. Run the Django development server:
```
python manage.py runserver
```
6. Run the fastapi in a separate terminal using:
```
Python app.py
```
7. Run the celery in a separate terminal using:
```
celery -A app.celery worker --loglevel=info
```
Note: for celery to work make sure that your redis server is running

### Test
1. For django user module test use the following command:
```
python manage.py test
```
2. For the test of fastapi i.e., task management use the command:
```
pytest unit_test.py
```
Note: there is some errors in the task management api tes, unfortunetly didn't get time to debug those.

### Endpoint:
1. Django: `http://127.0.0.1:8000/api/docs/`
2. Fastapi: `http://0.0.0.0:8001/docs`




