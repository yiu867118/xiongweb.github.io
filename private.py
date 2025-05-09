import re
from Crypto.PublicKey import RSA



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


