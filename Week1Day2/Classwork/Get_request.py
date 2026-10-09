import requests
url = 'https://jsonplaceholder.typicode.com/users'
response = requests.get(url)
print(response.json())


