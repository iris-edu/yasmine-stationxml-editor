# YASMINE Backend
If GUI is required to be used, please see `../frontend/README.md` before using backend

### Using python virtual environment
1. Install Python 3.6.5+
2. Run `python -m venv env`
3. Run `source env/bin/activate`
4. Run `pip install --upgrade pip setuptools`
5. Run `pip install -r requirements.txt`
6. Run `yasmineapp.py syncdb upgrade heads`
7. Run `yasmineapp.py runserver`

### Using Docker
1. Install Docker <https://www.docker.com/products/docker-desktop>
2. Build Docker image: `docker build -t yasmine/backend .`
3. Run Docker image: `docker run --rm -p 80:80 yasmine/backend`
4. Go to GUI url: <http://localhost>
5. Go to REST API endpoint: <http://localhost/api/>

### Tips
1. To generate a DB migration script: `python yasmineapp.py syncdb revision --autogenerate` 
2. To apply DB migrations: `python yasmineapp.py syncdb upgrade heads`
3. To run all unittests `python yasmineapp.py test`
