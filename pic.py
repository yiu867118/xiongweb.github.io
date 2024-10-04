import requests
from PIL import Image
from io import BytesIO

# 原图URL（去掉缩略图参数）
url = "https://pic.616pic.com/bg_w1180/00/05/76/3b2gmqPxdq.jpg"

# 下载图像
response = requests.get(url)
img = Image.open(BytesIO(response.content))

# 显示图像
img.show()

