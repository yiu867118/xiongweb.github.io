from flask import Flask, request, jsonify
from alipay import AliPay

app = Flask(__name__)

# 初始化支付宝SDK
alipay = AliPay(
    appid="2021004182631875",
    app_notify_url="http://127.0.0.1:5000/notify",  # 支付宝回调地址
    app_private_key_string=open("private.txt").read(),
    alipay_public_key_string=open("public.txt").read(),
    sign_type="RSA2",  # RSA 或者 RSA2
    debug=False  # 设置为True以访问沙箱环境
)

@app.route('/create_order', methods=['GET'])
def create_order():
    order_string = alipay.api_alipay_trade_app_pay(
        out_trade_no="订单号",
        total_amount="订单金额",
        subject="订单标题",
        return_url="http://127.0.0.1:5000/return",
        notify_url="http://127.0.0.1:5000/notify"  # 回调地址
    )
    return order_string

@app.route('/notify', methods=['POST'])
def notify():
    data = request.form.to_dict()
    signature = data.pop("sign")

    success = alipay.verify(data, signature)
    if success:
        # 在这里处理支付成功的逻辑，例如更新订单状态
        return "success"
    else:
        return "fail"

if __name__ == '__main__':
    app.run(port=5000)
