from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class Up(Resource):
    def get(self):
        return {"status" : "ok"}

api.add_resource(Up, '/_up')

if __name__ == '__main__':
    app.run(debug=True)