from flask import Flask, request, jsonify
from alipay import AliPay
import time

app = Flask(__name__)

# 初始化支付宝SDK
alipay = AliPay(
    appid="2021004182631875",
    app_notify_url="https://uppjbtoicickglnjorjn.supabase.co/functions/v1/notify",
    app_private_key_string=open("private.txt").read(),
    alipay_public_key_string=open("public.txt").read(),
    sign_type="RSA2"
)

@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    amount = data.get('amount')
    if not amount:
        return jsonify({'error': 'Amount is required'}), 400

    order_string = alipay.api_alipay_trade_app_pay(
        out_trade_no=f'order_{int(time.time())}',
        total_amount=str(amount),
        subject='红包支付',
        return_url='https://uppjbtoicickglnjorjn.supabase.co/functions/v1/return',
        notify_url='https://uppjbtoicickglnjorjn.supabase.co/functions/v1/notify'
    )
    return order_string

@app.route('/notify', methods=['POST'])
def notify():
    data = request.form.to_dict()
    signature = data.pop('sign')

    success = alipay.verify(data, signature)
    if success:
        # 处理支付成功的逻辑，例如更新订单状态
        return "success"
    else:
        return "fail"

if __name__ == '__main__':
    app.run(debug=True)
