from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient
import json
import os
import requests


def start_db():
    url = "http://localhost:7200/rest/repositories/bolsa"
    response = requests.delete(url)
    #print(response.status_code)
    print("GraphDB: Creating Repository")
    filepath = os.path.join("rdf", "repo-config.ttl")
    files = {
        'config': open(filepath, 'rb')
    }
    url = 'http://localhost:7200/rest/repositories'
    response = requests.post(url, files=files)
    #print(response.status_code)
    print("GraphDB: Adding data to Repository")
    filepath = os.path.join("rdf", "data.n3")
    headerParams = {"Content-Type": "text/rdf+n3;charset=UTF-8"}
    file = open(filepath, 'rb').read()
    url = 'http://localhost:7200/repositories/bolsa/statements'
    response = requests.post(url, data=file, headers=headerParams)
    #print(response.status_code)
    #print(response.text)
    #print(response)

# #OLD WAY (not working currently)
# def start_db():
#     endpoint = "http://localhost:7200"
#     repo_name = "bolsa"
#     client = ApiClient(endpoint=endpoint)
#     accessor = GraphDBApi(client)
#     accessor.delete_repository(repo_name=repo_name)
#     payload = {
#         "repositoryID": repo_name,
#         "label": "Description of your database",
#         "ruleset": "owl-horst-optimized"
#     }
#     res = accessor.create_repository(body=payload)
#     print(res)
#     filepath = os.path.join("rdf", "data.n3")
#     accessor.upload_data_file(filepath, repo_name=repo_name)
