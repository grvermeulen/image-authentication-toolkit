import requests

image_path = 'images/Visum pasfoto.jpg'
url = 'http://localhost:8080/'

with open(image_path, 'rb') as img:
    files = {'file': ('Visum pasfoto.jpg', img, 'image/jpeg')}
    response = requests.post(url, files=files)
    print('Status code:', response.status_code)
    print('Response text:', response.text) 