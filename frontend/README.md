# yasmine GUI

Frontend

## Compile GUI

### Using Sencha CMD

1. Install Sencha CMD <https://www.sencha.com/products/extjs/cmd-download/>.
2. **PROD**: Run the following to compile GUI for backend: `sencha app build`. The output will be placed in *../../backend/yasmine/static/js/yasmine*
3. **DEV**: Run the following to use Sencha watcher: `sencha app watch --j2ee`. All backend call will be redirected to <http://yasmine-backend:80/api>. See *WEB-INF/web.xml*

### Using Docker

1. Install Docker <https://www.docker.com/products/docker-desktop.>
2. Build Docker image: `docker build -t yasmine/sencha-cmd .`
    - If running alone without frontend, adding `--network yasmine` may be necessary
3. **PROD**: Run the following to compile GUI for backend: `docker run --rm -v "$(pwd)/../":/code yasmine/sencha-cmd sencha app build`. The output will be placed in *../../backend/yasmine/static/js/yasmine*
4. **DEV**: Run the following to use Sencha watcher: `docker run --rm -v "$(pwd)/../":/code yasmine/sencha-cmd`. All backend call will be redirected to <http://yasmine-backend:80/api>. See *WEB-INF/web.xml*
