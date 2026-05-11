import json
import urllib.error
import urllib.request

base = r"d:/Generative AI Professional/Assignment/Project/MedAgent"
reg_path = base + "/fullstack/backend/MedAgent.Api/tmp-reg.json"
out_path = base + "/fullstack/backend/MedAgent.Api/tmp-out3.json"
put_path = base + "/fullstack/backend/MedAgent.Api/tmp-put.json"
api = "http://127.0.0.1:5109"

# register
req = urllib.request.Request(
    f"{api}/api/Auth/register",
    data=open(reg_path, "rb").read(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as r:
    body = json.loads(r.read().decode())
token = body["token"]

req2 = urllib.request.Request(
    f"{api}/api/medical-id",
    data=open(put_path, "rb").read(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
    method="PUT",
)
try:
    with urllib.request.urlopen(req2) as r:
        print("STATUS", r.status)
        print(r.read().decode())
except urllib.error.HTTPError as e:
    print("STATUS", e.code)
    print(e.read().decode())
