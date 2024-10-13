const { Alipay } = require('alipay-sdk');
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient('https://uppjbtoicickglnjorjn.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVwcGpidG9pY2lja2dsbmpvcmpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjg2MzE4MDUsImV4cCI6MjA0NDIwNzgwNX0.TnPWSguzaNfyoR4lYNngiiCAOThjfhf19iOJsW2o__M');
const alipay = new Alipay({
  appId: '2021004182631875',
  privateKey: process.env.PRIVATE_KEY, // 从环境变量中读取私钥
  alipayPublicKey: process.env.ALIPAY_PUBLIC_KEY, // 从环境变量中读取支付宝公钥
  signType: 'RSA2',
  gateway: 'https://openapi.alipay.com/gateway.do',
});

exports.handler = async (req, res) => {
  try {
    const orderStr = alipay.tradeAppPay({
      outTradeNo: '订单号',
      totalAmount: '订单金额',
      subject: '订单标题',
      notifyUrl: 'https://uppjbtoicickglnjorjn.supabase.co/functions/v1/notify',
    });

    res.status(200).send(orderStr);
  } catch (error) {
    console.error('Error creating order:', error);
    res.status(500).send('Error creating order');
  }
};

