import requests

url = "https://jsonplaceholder.typicode.com/users"

response = requests.get(url)

data = response.json()

print("Status Code:", response.status_code)
# print("Response:", data)

for user in data:
    phone_ext = user["phone"].split("x")  # Extracting the first part of the phone number
    #print("Phone Extension:", phone_ext[1])
    if len(phone_ext) > 1:
        phone_ext = phone_ext[1]
    else:
        phone_ext= user["phone"].strip()  # Keep the phone number as is if no extension
    print("Name:", user["name"])
    print("Email:", user["email"])
    print("Company:", user["company"]["name"])
    print("Phone:", phone_ext)
    print("-" * 40)

# Using lambda function to format user information
#format_user = lambda u: f"{u['name']} | {u['email']} | {u['company']['name']}"
#for user in data:
#    print(format_user(user))