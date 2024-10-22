from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from supabase import create_client, Client
import requests
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import base64
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest

# Load Alipay keys
with open('private_pkcs1.pem', 'r') as f:
    alipay_private_key = f.read().strip()
with open('public_.txt', 'r') as f:
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
        'https://openapi.alipay.com/gateway.do',
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
    client_config = AlipayClientConfig()
    client_config.server_url = 'https://openapi.alipaydev.com/gateway.do'
    client_config.app_id = '2021004182631875'
    client_config.app_private_key = alipay_private_key
    client_config.alipay_public_key = alipay_public_key

    client = DefaultAlipayClient(alipay_client_config=client_config, logger=None)

    model = AlipayTradePrecreateModel()
    model.out_trade_no = order_id
    model.total_amount = amount
    model.subject = 'Red Envelope'

    request = AlipayTradePrecreateRequest(biz_model=model)
    request.notify_url = 'https://uppjbtoicickglnjorjn.supabase.co/functions/v1/notify'

    try:
        print("Executing request with timeout")
        response = client.execute(request)
        if response.is_success():
            print(f"QR Code: {response.qr_code}")
            return response.qr_code
        else:
            print(f"Error: {response}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
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
