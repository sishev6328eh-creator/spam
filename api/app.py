from flask import Flask, request, jsonify
import requests
from byte import Encrypt_ID, encrypt_api
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=50)

def fetch_tokens():
    """جلب أول 100 توكن من الرابط مباشرة"""
    try:
        response = requests.get("https://aauto-token.onrender.com/api/get_jwt", timeout=30)
        response.raise_for_status()
        data = response.json()
        tokens = data.get("tokens", {})
        # أخذ أول 100 توكن فقط
        first_100_tokens = dict(list(tokens.items())[:100])
        return first_100_tokens
    except Exception as e:
        print("Error fetching tokens:", e)
        return {}

def send_request(token, target_uid):
    target_uid_int = int(target_uid)
    id_encrypted = Encrypt_ID(target_uid_int)
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

    try:
        resp = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
        if resp.status_code == 200:
            return {"token_uid": token[:20]+"...", "status": "success"}
        else:
            return {"token_uid": token[:20]+"...", "status": "failed", "code": resp.status_code}
    except Exception as e:
        return {"token_uid": token[:20]+"...", "status": "error", "error": str(e)}

@app.route("/add_friend", methods=["GET"])
def add_friend():
    target_uid = request.args.get("uid")
    if not target_uid:
        return jsonify({"error": "Missing target uid"}), 400

    tokens = fetch_tokens()
    if not tokens:
        return jsonify({"error": "No tokens found"}), 500

    # إرسال الطلبات بالتوازي لكل التوكنات
    futures = [executor.submit(send_request, token, target_uid) for token in tokens.values()]
    results = [future.result() for future in as_completed(futures)]

    return jsonify({"target_uid": target_uid, "results": results, "total_requests": len(results)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
