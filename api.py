import os
from instalrest.v1.api import app, models
import instalrest.instalcelery.instalcelery
def create_default(app):
    print("CREATE DEFAULT")
    models.setup_tables()
    host = os.environ.get("INSTAL_FLASK_REST_HOST","0.0.0.0")
    port = os.environ.get("INSTAL_FLASK_REST_PORT","5000")
    debug = os.environ.get("INSTAL_FLASK_REST_DEBUG",False)
    if debug == "False":
        debug = False
    threads = os.environ.get("INSTAL_FLASK_REST_THREADS",1)
    return app

app_modified = create_default(app)

if __name__ == "__main__":
    app.run()