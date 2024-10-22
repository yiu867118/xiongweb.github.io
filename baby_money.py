import time
import requests
from urllib.parse import urlencode
import hashlib
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

import re

def clean_pem_key(key):
    # Remove all non-essential whitespace, ensuring proper formatting
    key = key.replace("-----BEGIN RSA PRIVATE KEY-----", "").replace("-----END RSA PRIVATE KEY-----", "")
    key = key.replace(" ", "").replace("\n", "").replace("BEGINRSAPRIVATEKEY", "").replace("ENDRSAPRIVATEKEY", "")
    key = re.sub(r'(?=.{64})(.{64})', r'\1\n', key)  # Insert line breaks every 64 characters
    key = f"-----BEGIN RSA PRIVATE KEY-----\n{key}\n-----END RSA PRIVATE KEY-----"
    return key

with open('private_pkcs1.pem', 'r') as f:
    raw_key = f.read().strip()
    alipay_private_key = clean_pem_key(raw_key)
    print(alipay_private_key)  # 打印转换后的私钥，确保格式正确

with open('public.txt', 'r') as f:
    alipay_public_key = f.read().strip()

# 验证格式是否正确
try:
    RSA.import_key(alipay_private_key)
    print("The private key format is good.")
except ValueError as e:
    print(f"Error with private key format: {e}")

    

with open('private_pkcs1.pem', 'r') as f:
    raw_key = f.read().strip()
    alipay_private_key = clean_pem_key(raw_key)

with open('public.txt', 'r') as f:
    alipay_public_key = f.read().strip()


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 确保 CORS 配置正确，允许所有域名访问

supabase_url = 'https://uppjbtoicickglnjorjn.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVwcGpidG9pY2lja2dsbmpvcmpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjg2MzE4MDUsImV4cCI6MjA0NDIwNzgwNX0.TnPWSguzaNfyoR4lYNngiiCAOThjfhf19iOJsW2o__M'
supabase: Client = create_client(supabase_url, supabase_key)

def verify_alipay_signature(data, signature):
    key = RSA.importKey(alipay_public_key)
    h = SHA256.new(data.encode('utf-8'))
    verifier = PKCS1_v1_5.new(key)
    return verifier.verify(h, base64.b64decode(signature))

@app.route('/alipay/check-payment', methods=['POST'])
def check_payment():
    req_data = request.get_json()
    order_id = req_data.get('orderId')

    alipay_response = requests.post(
        'https://openapi.alipaydev.com/gateway.do',
        data={
            'app_id': '2021004182631875',
            'method': 'alipay.trade.query',
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': '2017-04-14 00:00:00',
            'version': '1.0',
            'biz_content': json.dumps({
                'out_trade_no': order_id,
                'trade_no': 'transaction_id'
            })
        },
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )

    if alipay_response.status_code == 200:
        response_data = alipay_response.json()
        if response_data['alipay_trade_query_response']['trade_status'] == 'TRADE_SUCCESS':
            return jsonify({'success': True, 'amount': response_data['alipay_trade_query_response']['total_amount']})
    
    return jsonify({'success': False}), 400


@app.route('/alipay/create-payment', methods=['POST'])
def create_payment():
    print("Received request for create-payment")  # 添加调试信息
    req_data = request.get_json()
    amount = req_data.get('amount')
    
    order_id = generate_order_id()
    qr_code_url = generate_qr_code_url(order_id, amount)
    print(f"Generated QR Code URL: {qr_code_url}")  # 添加调试信息

    if qr_code_url:
        return jsonify({
            'success': True,
            'qrCodeUrl': qr_code_url,
            'orderId': order_id
        })
    else:
        return jsonify({'success': False}), 500

def generate_order_id():
    import uuid
    return str(uuid.uuid4())

def generate_qr_code_url(order_id, amount):
    url = 'https://openapi.alipaydev.com/gateway.do'

    biz_content = json.dumps({
        "out_trade_no": order_id,
        "total_amount": amount,
        "subject": "Red Envelope",
        "product_code": "QUICK_MSECURITY_PAY"
    })

    data = {
        "app_id": "2021004182631875",
        "method": "alipay.trade.precreate",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "biz_content": biz_content
    }

    # 对 data 进行签名
    try:
        data["sign"] = sign_data(data)
        print("Request data:", data)
        response = retry_request(url, data)
        if response:
            response_json = response.json()
            print("Response JSON:", response_json)

            if response_json["alipay_trade_precreate_response"]["code"] == "10000":
                qr_code_url = response_json["alipay_trade_precreate_response"]["qr_code"]
                print(f"QR Code: {qr_code_url}")
                return qr_code_url
            else:
                print(f"Error: {response_json}")
                return None
        else:
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def sign_data(data):
    ordered_data = sorted([(k, v) for k, v in data.items()])
    unsigned_string = "&".join(f"{k}={v}" for k, v in ordered_data)
    return sign_with_rsa2(unsigned_string, alipay_private_key)

def sign_with_rsa2(unsigned_string, private_key):
    key = RSA.import_key(private_key)
    h = SHA256.new(unsigned_string.encode('utf-8'))
    signer = PKCS1_v1_5.new(key)
    return base64.b64encode(signer.sign(h)).decode('utf-8')

def retry_request(url, data, retries=3, delay=1, timeout=60):
    for i in range(retries):
        try:
            print(f"Attempt {i + 1}: Sending request")
            start_time = time.time()  # 开始时间
            response = requests.post(url, data=urlencode(data), headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=timeout)
            end_time = time.time()  # 结束时间
            print(f"Attempt {i + 1}: Request completed in {end_time - start_time} seconds")
            if response.status_code == 200:
                return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {i + 1} failed: {e}")
            time.sleep(delay)
    return None

@app.route('/save-record', methods=['POST'])
def save_record():
    data = request.get_json()
    username = data.get('username')
    amount = data.get('amount')
    page_url = request.referrer

    response = supabase.table('visits').insert({
        'username': username,
        'page_url': page_url,
        'amount': amount
    }).execute()

    if response.status_code == 201:
        return jsonify({'success': True})
    return jsonify({'success': False}), 500

if __name__ == '__main__':
    app.run(debug=True)
