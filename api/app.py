from flask import Flask, request, jsonify
import requests
from byte import Encrypt_ID, encrypt_api
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=50)

# قائمة الإيديات المطلوبة (50 ID)
TARGET_IDS = [
    4182940828, 4182940823, 4182940830, 4182940837, 4182940841,
    4182940835, 4182940827, 4182940825, 4182940843, 4182940836,
    4182940842, 4182940831, 4182940826, 4182940824, 4182940840,
    4182940832, 4182940822, 4182940833, 4182940834, 4182940829,
    4182943566, 4182943556, 4182943559, 4182943562, 4182943571,
    4182943572, 4182943574, 4182943568, 4182943557, 4182943569,
    4182943560, 4182943570, 4182943561, 4182943573, 4182943555,
    4182943563, 4182943564, 4182943565, 4182943558, 4182943567,
    4182944867, 4182944869, 4182944868, 4182944871, 4182944866,
    4182944877, 4182944874, 4182944880, 4182944878, 4182944873,
]

def fetch_tokens():
    """جلب التوكنات للإيديات المطلوبة فقط"""
    try:
        response = requests.get("https://auto-token-spmmm.onrender.com/api/get_jwt", timeout=30)
        response.raise_for_status()
        data = response.json()
        tokens = data.get("tokens", {})

        # فلترة فقط الإيديات اللي نحتاجها
        filtered_tokens = {uid: tokens[str(uid)] for uid in TARGET_IDS if str(uid) in tokens}
        return filtered_tokens
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

    # إرسال الطلبات للتوكنات المفلترة فقط
    futures = [executor.submit(send_request, token, target_uid) for token in tokens.values()]
    results = [future.result() for future in as_completed(futures)]

    return jsonify({"target_uid": target_uid, "results": results, "total_requests": len(results)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
