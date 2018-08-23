from peewee import Model, PostgresqlDatabase, ForeignKeyField, TextField, CharField, IntegerField
from marshmallow import fields, schema, post_load
from playhouse.postgres_ext import ArrayField, JSONField
from io import StringIO
import instal
from playhouse.shortcuts import model_to_dict
import simplejson as json
from tempfile import NamedTemporaryFile
import time
import random
import instalrest.instalcelery.instalcelery

database = PostgresqlDatabase(
    'instal-rest-v1',  
    user='instal', 
    password='instal', 
    host='instal-db',
    port=5432
)
class BaseModel(Model):
    class Meta:
        database = database

class InstALModel(BaseModel):
    institutions = ArrayField(TextField,index=False)
    bridges = ArrayField(TextField,index=False)
    logic_programming = ArrayField(TextField,index=False)
    facts = ArrayField(TextField,index=False)
    @classmethod
    def get_marshelled_dict(cls,data):
        return cls.ModelSchema().load(data)

    @classmethod
    def new_from_form_data(cls, data) -> "InstALModel":
        marshelled = cls.get_marshelled_dict(data)
        di = marshelled.data
        new_model = cls(institutions=di.get("institutions",[]),bridges=di.get("bridges",[]),logic_programming=di.get("logic_programs",[]),facts=di.get("facts",[]))
        new_model.save()
        return new_model

    class ModelSchema(schema.Schema):
        institutions = fields.List(fields.String(),required=True)
        bridges = fields.List(fields.String())
        logic_programs = fields.List(fields.String())
        facts = fields.List(fields.String())

        @post_load
        def make_model(self, data):
            pass

    def to_dict(self):
        return model_to_dict(self,recurse=True)

    def to_json(self):
        return json.dumps(self.to_dict())

    def get_inspect(self):
        ial_files = [StringIO(s) for s in self.institutions]
        bridge_files = [StringIO(s) for s in self.bridges]
        logic_programs = [StringIO(s) for s in self.logic_programming]
        inspect = instal.instalinspect.instal_inspect_files(ial_files=ial_files, bridge_files=bridge_files,
                                                    lp_files=logic_programs, domain_files=[],
                                                    query_file=[],
                                                    fact_files=[])
        return inspect


class InstALGrounding(BaseModel):
    model = ForeignKeyField(InstALModel, related_name="groundings")
    types = JSONField()
    facts = ArrayField(TextField,index=False)
    #types
    class GroundingSchema(schema.Schema):
        types = fields.Dict(required=False)
        facts = fields.List(fields.String())

    @classmethod
    def get_marshelled_dict(cls, data):
        return cls.GroundingSchema().load(data)

    @classmethod
    def new_from_form_data(cls, data, model_id) -> "InstALGrounding":
        marshelled = cls.get_marshelled_dict(data)
        di = marshelled.data
        new_grounding = cls(model_id=model_id, types=di.get("types",{}),facts=di.get("facts",[]))
        new_grounding.save()
        return new_grounding

    def get_domain_text(self):
        outstr = ""
        for k, v in self.types.items():
            outstr += "{}: ".format(k.title())
            for val in v:
                outstr += val + " "
            outstr += "\n"
        return outstr

    def to_dict(self):
        return model_to_dict(self,recurse=True)

    def to_json(self):
        return json.dumps(self.to_dict())

class InstALQuery(BaseModel):
    grounding = ForeignKeyField(InstALGrounding, related_name="queries")
    query = ArrayField(CharField,index=False)
    facts = ArrayField(TextField,index=False)
    length = IntegerField(default=0)
    number = IntegerField(default=1)
    json_out = JSONField(default=[])
    status = CharField(default="running")
    errors = ArrayField(TextField,default=[],index=False)
    logic_programming = ArrayField(TextField,index=False)

    class AnswerSetNotFound(Exception):
        pass

    class AnswerSetRepresentationNotFound(Exception):
        pass

    def n_answer_sets(self):
        return len(self.json_out)

    class QuerySchema(schema.Schema):
        query = fields.List(fields.String())
        length = fields.Integer()
        facts = fields.List(fields.String())
        number = fields.Integer()
        logic_programs = fields.List(fields.String())


    def output_from_form_data(self, rq, answer_set_number):
        if answer_set_number > len(self.json_out):
            raise AnswerSetNotFound
        answer_set = self.json_out[answer_set_number-1]
        accept = rq.headers.get("Accept",'application/json')
        if accept == "application/json":
            return (json.dumps(answer_set), 'application/json')
        elif accept == "text/plain":
            return (instalrest.instalcelery.instalcelery.get_instal_trace_text(answer_set), 'text/plain')
        else:
            raise AnswerSetRepresentationNotFound


    def to_dict(self):
        return model_to_dict(self,exclude=["json_out"],extra_attrs=["n_answer_sets"],recurse=True)

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def get_marshelled_dict(cls, data):
        return cls.QuerySchema().load(data)

    @classmethod
    def new_from_form_data(cls, data, grounding_id) -> "InstALQuery":
        marshelled = cls.get_marshelled_dict(data)
        di = marshelled.data
        new_query = cls(grounding_id=grounding_id,length=di.get("length",0),query=di.get("query",[]),
                        facts=di.get("facts",[]),number=di.get("number",1),logic_programming=di.get("logic_programs",[]))
        new_query.save()
        return new_query

    def execute_instal(self) -> None:
        ial_files = [StringIO(s) for s in self.grounding.model.institutions]
        bridge_files = [StringIO(s) for s in self.grounding.model.bridges]
        logic_programs = [StringIO(s) for s in self.grounding.model.logic_programming] + [StringIO(s) for s in self.logic_programming]
        domains = [StringIO(self.grounding.get_domain_text())]
        query_file = StringIO(self.get_query_text())
        fact_files = [StringIO(s) for s in self.facts] + [StringIO(s) for s in self.grounding.facts] + [StringIO(s) for s in self.grounding.model.facts]
        try:
            out = instal.instalquery.instal_query_files(ial_files=ial_files,bridge_files=bridge_files,
                                                    lp_files=logic_programs,domain_files=domains,query_file=query_file,
                                                    fact_files=fact_files,
                                                    length=self.length, number=self.number)
            self.json_out = []
            for o in out: self.json_out.append(o.to_json())
            self.status = "complete"
        except Exception as e:
            self.errors = [str(type(e).__name__)] + list(e.args)
            self.status = "error"
        finally:
            self.save()

    def get_query_text(self):
        outstr = ""
        for s in self.query:
            outstr += "observed({})\n".format(s)
        return outstr

def setup_tables():
    t = 10
    connected = False
    while t > 0 and not connected:
        try:
            print("Running initial database setup")
            database.connect()
            connected = True
        except:
            t -= 1
            print("Database connect failure. Sleeping for 2 seconds. Trying again {} times...".format(t))
            time.sleep(2)

    try:
        print("Attempting to create database tables...")
        InstALModel.create_table()
        InstALGrounding.create_table()
        InstALQuery.create_table()
    except:
        print("...but presumably they're already created.")
        database.rollback()
