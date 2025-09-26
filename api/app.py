from flask import Flask, request, jsonify
import requests
import threading
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

def fetch_tokens_from_api():
    url = "https://aauto-token.onrender.com/api/get_jwt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tokens_dict = data.get("tokens", {})
        tokens_list = [(uid, token) for uid, token in list(tokens_dict.items())[:500]]
        return tokens_list
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

def send_friend_request(uid, region, token, results, lock, stop_event):
    if stop_event.is_set():
        return
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "16",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }
    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        with lock:
            if response.status_code == 200:
                results["success"] += 1
                if results["success"] >= 50:
                    stop_event.set()
            else:
                results["failed"] += 1
    except Exception as e:
        print(f"Error sending request for region {region} with token {token}: {e}")
        with lock:
            results["failed"] += 1

@app.route("/send_requests", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400

    tokens_with_region = fetch_tokens_from_api()
    if not tokens_with_region:
        return jsonify({"error": "No tokens fetched from API"}), 1000

    results = {"success": 0, "failed": 0}
    threads = []
    lock = threading.Lock()
    stop_event = threading.Event()

    for region, token in tokens_with_region:
        if stop_event.is_set():
            break
        thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results, lock, stop_event))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    status = 1 if results["success"] != 0 else 2
    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
