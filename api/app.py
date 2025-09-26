from flask import Flask, request, jsonify
import requests
from byte import Encrypt_ID, encrypt_api
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=50)

# قائمة الـUIDs التي تريد استخدامها فقط
UIDS_TO_USE = [
    "4182940828","4182940823","4182940830","4182940837","4182940841",
    "4182940835","4182940827","4182940825","4182940843","4182940836",
    "4182940842","4182940831","4182940826","4182940824","4182940840",
    "4182940832","4182940822","4182940833","4182940834","4182940829",
    "4182943566","4182943556","4182943559","4182943562","4182943571",
    "4182943572","4182943574","4182943568","4182943557","4182943569",
    "4182943560","4182943570","4182943561","4182943573","4182943555",
    "4182943563","4182943564","4182943565","4182943558","4182943567",
    "4182944867","4182944869","4182944868","4182944871","4182944866",
    "4182944877","4182944874","4182944880","4182944878","4182944873"
]

def fetch_tokens():
    """جلب التوكنات من الرابط وتصفيتها حسب UIDS_TO_USE"""
    response = requests.get("https://aauto-token.onrender.com/api/get_jwt")
    if response.status_code == 200:
        data = response.json()
        tokens = data.get("tokens", {})
        # فلترة التوكنات بحيث تكون فقط للعناصر التي بالـUIDS_TO_USE
        filtered_tokens = {uid: tokens[uid] for uid in UIDS_TO_USE if uid in tokens}
        return filtered_tokens
    else:
        return {}

def send_request(token, uid):
    uid = int(uid)
    id_encrypted = Encrypt_ID(uid)
    data0 = "08c8b5cfea1810" + id_encrypted + "18012008"
    data = bytes.fromhex(encrypt_api(data0))

    url = "https://clientbp.common.ggbluefox.com/RequestAddingFriend"
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
        'Connection': 'Keep-Alive',
        'Expect': '100-continue',
        'Authorization': f'Bearer {token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB50',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(url, headers=headers, data=data, verify=False)
    if response.status_code == 200:
        return {"status": "success", "message": "Friend request sent!"}
    else:
        return {"status": "failed", "code": response.status_code, "response": response.text}

@app.route("/add_friend", methods=["GET"])
def add_friend():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    # فقط نفذ إذا كان uid ضمن القائمة المسموحة
    if uid not in UIDS_TO_USE:
        return jsonify({"error": "UID not allowed"}), 403

    tokens = fetch_tokens()
    token = tokens.get(uid)
    if not token:
        return jsonify({"error": "Token not found for this UID"}), 404

    future = executor.submit(send_request, token, uid)
    result = future.result()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
