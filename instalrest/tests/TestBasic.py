from unittest import TestCase
import requests
import simplejson as json
import time

INSTAL_URL = "http://127.0.0.1:5000"
class Basic(TestCase):
    def test_query_execute(self):
        model_response = requests.post(INSTAL_URL + "/model/",headers={'Content-Type': 'application/json'},
                                       data=json.dumps({"institutions": ["institution a; exogenous event e; initially pow(e);" ] }))
        assert(model_response.status_code==201)
        model_response_json = json.loads(model_response.content)
        assert(model_response_json.get("id",0))

        grounding_response = requests.post(INSTAL_URL + "/model/{}/grounding/".format(model_response_json["id"]),data=json.dumps({}),headers={'Content-Type': 'application/json'})
        assert(grounding_response.status_code==201)
        grounding_response_json = json.loads(grounding_response.content)
        assert(grounding_response_json.get("id",0))

        query_response = requests.post(INSTAL_URL + "/model/{}/grounding/{}/query/".format(model_response_json["id"],grounding_response_json["id"]),
                                       headers={'Content-Type': 'application/json'},data=json.dumps({"query" : ["observed(e)"]}))
        assert(query_response.status_code==201)
        query_response_json = json.loads(query_response.content)
        assert(query_response_json.get("id",0))
        #assert(query_response_json.get("json_out",{}))

        time.sleep(3)
        response = requests.get(INSTAL_URL + "/model/{}/grounding/{}/query/{}/output/1/".format(
            query_response_json.get("grounding", {}).get("model", {}).get("id"), query_response_json.get("grounding", {}).get("id"),
            query_response_json.get("id")
        )
                                ,
                                data=json.dumps(
                                    {"type": "json"}
                                ),
                                headers={'Content-Type': 'application/json'})

        assert (response.status_code == 200)

    def test_query_more_complicated(self):
        model_response = requests.post(INSTAL_URL + "/model/",
                                       data=json.dumps({"institutions": ["institution a; type A; exogenous event ex_a(A); inst event in_a(A); initially pow(ex_a(A)), perm(ex_a(A)), perm(in_a(A));",
                                                              "institution c; type A; exogenous event ex_b(A); initially pow(ex_b(A));"],
                                             "bridges" : ["bridge b; source a; sink c; in_a(A) xgenerates ex_b(A); initially gpow(a, ex_b(A), c);"]}),
                                       headers={'Content-Type': 'application/json'})
        assert(model_response.status_code==201)
        model_response_json = json.loads(model_response.content)
        assert(model_response_json.get("id",0))

        grounding_response = requests.post(INSTAL_URL + "/model/{}/grounding/".format(model_response_json["id"]), data=json.dumps({"types" : {"A" : ["alpha", "beta"]}}),
                                           headers={'Content-Type': 'application/json'})
        assert(grounding_response.status_code==201)
        grounding_response_json = json.loads(grounding_response.content)
        assert(grounding_response_json.get("id",0))

        query_response = requests.post(INSTAL_URL + "/model/{}/grounding/{}/query/".format(model_response_json["id"],grounding_response_json["id"]),
                                       data=json.dumps({"query" : []}),
                                       headers = {'Content-Type': 'application/json'})
        assert(query_response.status_code==201)
        query_response_json = json.loads(query_response.content)
        assert(query_response_json.get("id",0))
        assert(query_response_json.get("json_out",{}))
        time.sleep(3)
        response = requests.get(INSTAL_URL + "/model/{}/grounding/{}/query/{}/output/1/".format(
            query_response_json.get("grounding", {}).get("model", {}).get("id"), query_response_json.get("grounding", {}).get("id"),
            query_response_json.get("id")
        )
                                ,
                                data=json.dumps(
                                    {"type": "json"}
                                ),
                                headers={'Content-Type': 'application/json'})

        assert (response.status_code == 200)

    def test_new_basic(self):
        query_response = requests.post(INSTAL_URL + "/new/",
                                       data = json.dumps({
                                           "institutions": [
                                               "institution a; type A; exogenous event ex_a(A); inst event in_a(A); initially pow(ex_a(A)), perm(ex_a(A)), perm(in_a(A));",
                                               "institution c; type A; exogenous event ex_b(A); initially pow(ex_b(A));"],
                                           "bridges": [
                                               "bridge b; source a; sink c; in_a(A) xgenerates ex_b(A); initially gpow(a, ex_b(A), c);"],
                                           "types": {"A": ["alpha", "beta"]},
                                           "query": ["ex_a(alpha)", "ex_a(beta)"]
                                               }),
                                       headers= {'Content-Type' : 'application/json'})
        assert(query_response.status_code==201)

        json_resp = query_response.json()
        time.sleep(3)
        response = requests.get(INSTAL_URL + "/model/{}/grounding/{}/query/{}/output/1/".format(
            json_resp.get("grounding", {}).get("model", {}).get("id"), json_resp.get("grounding", {}).get("id"),
            json_resp.get("id")
        )
                                ,
                                headers={'Accept' : 'application/json'})

        assert (response.status_code == 200)

    def test_get_text(self):
        query_response = requests.post(INSTAL_URL + "/new/",
                                       data=json.dumps({
                                           "institutions": [
                                               "institution a; type A; exogenous event ex_a(A); inst event in_a(A); initially pow(ex_a(A)), perm(ex_a(A)), perm(in_a(A));",
                                               "institution c; type A; exogenous event ex_b(A); initially pow(ex_b(A));"],
                                           "bridges": [
                                               "bridge b; source a; sink c; in_a(A) xgenerates ex_b(A); initially gpow(a, ex_b(A), c);"],
                                           "types": {"A": ["alpha", "beta"]},
                                           "query": ["ex_a(alpha)", "ex_a(beta)"]
                                       }),
                                       headers={'Content-Type': 'application/json'})
        assert (query_response.status_code == 201)

        json_resp = query_response.json()
        time.sleep(3)
        response = requests.get(INSTAL_URL + "/model/{}/grounding/{}/query/{}/output/1/".format(
            json_resp.get("grounding", {}).get("model", {}).get("id"), json_resp.get("grounding", {}).get("id"),
            json_resp.get("id")
        )
                                ,
                                headers={'Accept': 'text/plain'})

        assert (response.status_code == 200)