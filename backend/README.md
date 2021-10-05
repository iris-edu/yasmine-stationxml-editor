# YASMINE Backend
If GUI is required to be used, please see `../frontend/README.md` before using backend

## For Users
### Using locally installed Python
1. Install Python 3.6.5+
2. Install numpy>=1.6.1
3. Run `pip install -r requirements.txt` to install dependencies
4. Run `python yasmineapp.py syncdb upgrade heads` to migrate database
5. Start application `python yasmineapp.py runserver`

### Using Docker
1. Install Docker <https://www.docker.com/products/docker-desktop>
2. Build Docker image: `docker build -t yasmine/backend .`
3. Run Docker image: `docker run --rm -p 80:80 yasmine/backend`
4. Go to GUI url: <http://localhost>
5. Go to REST API endpoint: <http://localhost/api/>

## For Developers
### Using locally installed Python
1. Install Python 3.6.5+
2. Install numpy>=1.6.1   
3. (optional) Selenium FireFox driver <https://github.com/mozilla/geckodriver/releases> should be added to the system path
4. Run `pip install -r requirements.txt` to install dependencies
5. (optional) Run `python yasmineapp.py syncdb revision --autogenerate` to create migration script
6. Run `python yasmineapp.py syncdb upgrade heads` to migrate database
7. (optional) Run `python yasmineapp.py test` to run tests
8. Start application `python yasmineapp.py runserver`

### Using Docker
1. Install Docker <https://www.docker.com/products/docker-desktop>
2. Build Docker image: `docker build -t yasmine/backend .`
3. Run Docker image: `docker run --rm -p 80:80 yasmine/backend`
4. Go to GUI url: <http://localhost>
5. Go to REST API endpoint: <http://localhost/api/>
