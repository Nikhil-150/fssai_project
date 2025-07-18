import requests

registration_number = "116574583"

# Step 1: Login to app form access
login_url = f"https://foscos.fssai.gov.in/gateway/fbo_readonly/getlogintofortacereg/{registration_number}"

# Step 2: Download Registration Certificate
registration_url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{registration_number}"

# Step 3: Download Application Form
application_form_url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/forma/{registration_number}"

# Reuse headers/cookies from curl
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://foscos.fssai.gov.in/",
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIyMDUyMTAzMTAwMDc5NSBmb3Njb3MuZnNzYWkuZ292LmluIDEwMy4yNDcuNi4xMzYgIiwiYXV0aG9yaXRpZXMiOlsiUk9MRV9GQk8iXSwidXNlcklkIjoiNjkzNjE5NTEiLCJpYXQiOjE3NTI4NTEzNTEsImV4cCI6MTc1MjkzNzc1MX0.31rf34hW5ZXLfhkxOFJfVhDPpffCeiVJ_YIHyZOPxUiPhWe0ou1S5GUqNGCK9I5ya0YGEyiE3GHmsUu5G_e6_A",
    "x-auth-user-id": "f33RY6DAyt+WQt8UJG54SQUxr5GrXYXkSwv4uzKRUiI=",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0"
}

cookies = {
    "_ga": "GA1.3.1387273733.1752841346",
    "_gid": "GA1.3.1395180104.1752841346",
    "_ga_E101FG0RXN": "GS2.3.s1752850885$o4$g1$t1752851351$j60$l0$h0",
    f"key_20521031000795": "ZFPF3b4Rwihz9PiHWxvfJ8ou2rb8NjE8rGW9nMy/hmA=",
    "_ga_X6L29149T6": "GS2.3.s1752841503$o1$g1$t1752842990$j19$l0$h0",
    "_gat": "1"
}

session = requests.Session()
session.headers.update(headers)
session.cookies.update(cookies)

# STEP 1: Initiate application session
login_response = session.get(login_url)
print("Step 1: Init session", login_response.status_code)

# STEP 2: Download Registration Certificate
reg_response = session.get(registration_url)
if reg_response.status_code == 200:
    with open(f"registration_{registration_number}.pdf", "wb") as f:
        f.write(reg_response.content)
    print("✅ Registration Certificate downloaded.")
else:
    print(f"❌ Registration download failed: {reg_response.status_code}")

# STEP 3: Download Application Form
app_response = session.get(application_form_url)
if app_response.status_code == 200:
    with open(f"application_form_{registration_number}.pdf", "wb") as f:
        f.write(app_response.content)
    print("✅ Application Form downloaded.")
else:
    print(f"❌ Application form download failed: {app_response.status_code}")
