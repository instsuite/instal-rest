import os
from flask import Flask, request, make_response
from flask_restful import Resource, Api, abort
from playhouse.shortcuts import model_to_dict
from instalrest.v1 import models
import simplejson as json
import instalrest
from instalrest.instalcelery.instalcelery import execute_instal_async, get_instal_inspect, celery_app
from peewee import DoesNotExist
app = Flask(__name__)
api = Api(app)

def make_response_json(data, code):
    rq = make_response(data,code)
    rq.headers["Content-Type"] = 'application/json'
    return rq

def make_response_text(data, code):
    rq = make_response(data, code)
    rq.headers["Content-Type"] = 'text/plain'
    return rq

class InstALModelList(Resource):
    @api.representation('application/json')
    def post(self):
        model = models.InstALModel.new_from_form_data(request.get_json())
        return make_response_json(model.to_json(), 201)

    @api.representation('application/json')
    def get(self):
        model = list(map(model_to_dict, models.InstALModel.select()))
        return make_response_json(json.dumps(model), 200)

class InstALModelInspect(Resource):
    @api.representation('application/json')
    def get(self, model_id):
        try:
            model = models.InstALModel.get(id=model_id)
            return make_response_json(json.dumps(get_instal_inspect(model_id)),200)
        except DoesNotExist as e:
            abort(404)


class InstALModel(Resource):
    @api.representation('application/json')
    def get(self, model_id):
        try:
            model = models.InstALModel.get(id=model_id)
            return make_response_json(model.to_json(), 200)
        except DoesNotExist as e:
            abort(404)

class InstALGroundingList(Resource):
    @api.representation('application/json')
    def get(self, model_id):
        try:
            grounding = list(map(model_to_dict, models.InstALGrounding.select().where(
                models.InstALGrounding.model == model_id)))
            return make_response_json(json.dumps(grounding),200)
        except DoesNotExist as e:
            abort(404)

    @api.representation('application/json')
    def post(self, model_id):
        try:
            grounding = models.InstALGrounding.new_from_form_data(request.get_json(), model_id)
            return make_response_json(grounding.to_json(),201)
        except DoesNotExist as e:
            abort(404)


class InstALGrounding(Resource):
    @api.representation('application/json')
    def get(self, model_id, grounding_id):
        try:
            grounding = models.InstALGrounding.get(id=grounding_id)
            return make_response_json(grounding.to_json(),201)
        except DoesNotExist as e:
            abort(404)

class InstALQueryList(Resource):
    @api.representation('application/json')
    def get(self, model_id, grounding_id):
        query = list(map(model_to_dict, models.InstALQuery.select().where(
            models.InstALQuery.grounding == grounding_id)))
        return make_response_json(json.dumps(query),200)

    @api.representation('application/json')
    def post(self, model_id, grounding_id):
        new_query = models.InstALQuery.new_from_form_data(request.get_json(), grounding_id)
        execute_instal_async.delay(new_query.id)
        return make_response_json(new_query.to_json(),201)


class InstALQuery(Resource):
    @api.representation('application/json')
    def get(self, model_id, grounding_id, query_id):
        try:
            query = models.InstALQuery.get(id=query_id)
            return make_response_json(query.to_json(),200)
        except DoesNotExist as e:
            abort(404)

class InstALOutput(Resource):
    @api.representation('application/json')
    def get(self, model_id, grounding_id, query_id, answer_set_id):
        query = models.InstALQuery.get(id=query_id)
        try:
            data, mimetype = query.output_from_form_data(request, answer_set_number=answer_set_id)
        except query.AnswerSetNotFound as e:
            abort(404)
            return
        except query.AnswerSetRepresentationNotFound as e:
            abort(417)
            return
        if mimetype == 'application/json':
            rq = make_response_json(data, 200)
        elif mimetype == 'text/plain':
            rq = make_response_text(data,200)
        else:
            abort(417)
            return
        return rq

class InstALNew(Resource):
    @api.representation('application/json')
    def post(self):
        new_model = models.InstALModel.new_from_form_data(request.get_json())
        new_grounding = models.InstALGrounding.new_from_form_data(request.get_json(),new_model.id)
        new_query = models.InstALQuery.new_from_form_data(request.get_json(),new_grounding.id)
        execute_instal_async.delay(new_query.id)
        return make_response_json(json.dumps(model_to_dict(new_query)),201)


class Up(Resource):
    @api.representation('application/json')
    def get(self):
        return make_response_json(json.dumps({"status" : "ok",
                                              "instalrest_version" : instalrest.__version__,
                                              "total_queries" : models.InstALQuery.select().count(),
                                              "total_groundings" : models.InstALGrounding.select().count(),
                                              "total_models" : models.InstALModel.select().count()
                                              }), 200)

def add_resources(api):
    api.add_resource(Up, '/_up')

    api.add_resource(InstALModelList, '/model/')
    api.add_resource(InstALModel, '/model/<int:model_id>/')
    api.add_resource(InstALModelInspect, '/model/<int:model_id>/inspect/')
    api.add_resource(InstALGroundingList, '/model/<int:model_id>/grounding/')
    api.add_resource(InstALGrounding, '/model/<int:model_id>/grounding/<int:grounding_id>/')
    api.add_resource(InstALQueryList, '/model/<int:model_id>/grounding/<int:grounding_id>/query/')
    api.add_resource(InstALQuery, '/model/<int:model_id>/grounding/<int:grounding_id>/query/<int:query_id>/')
    api.add_resource(InstALOutput,
                     '/model/<int:model_id>/grounding/<int:grounding_id>/query/<int:query_id>/output/<int:answer_set_id>/')

    api.add_resource(InstALNew, '/new/')
api = add_resources(api)