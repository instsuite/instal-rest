from celery import Celery
from instalrest.v1 import models
from tempfile import NamedTemporaryFile
import instal
import simplejson as json
celery_app = Celery('instal-rest', broker='amqp://instal:instal@instal-rabbit:5672//')

@celery_app.task
def execute_instal_async(instalQuery):
    query = models.InstALQuery.get(id=instalQuery)
    query.execute_instal()

@celery_app.task
def get_instal_trace_text(as_json):
    json_file = NamedTemporaryFile("w+t")
    json_file.write(json.dumps(as_json))
    json_file.seek(0)
    text_out = NamedTemporaryFile("w+t")
    instal.instaltrace.instal_trace_keyword(json_file=json_file.name, text_file=text_out.name)
    text_out.seek(0)
    return text_out.read()

@celery_app.task
def get_instal_inspect(instalModel):
    model = models.InstALModel.get(id=instalModel)
    return model.get_inspect()