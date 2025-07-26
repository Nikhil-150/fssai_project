import requests

registration_number = ["107417231", "106479978", "106480027", "106480148"]

# Step 1: Login to app form access


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
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIyMDUyMTAzMTAwMDc5NSBmb3Njb3MuZnNzYWkuZ292LmluIDEwMy4yNDcuNy4yMDYgIiwiYXV0aG9yaXRpZXMiOlsiUk9MRV9GQk8iXSwidXNlcklkIjoiNjkzNjE5NTEiLCJpYXQiOjE3NTM1MTYyMzIsImV4cCI6MTc1MzYwMjYzMn0.ogm7LPOcMXB8aqGwkvPH2G9HtRiY8qdTxhKPXGqoRtVOz6VGXHB0T2eqd9GpeGg1jA_aogIEoiVBoWK_F7QFag",
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


# STEP 2: Download Registration Certificate
# reg_response = session.get(registration_url)
# if reg_response.status_code == 200:
#     with open(f"registration_{registration_number}.pdf", "wb") as f:
#         f.write(reg_response.content)
#     print("✅ Registration Certificate downloaded.")
# else:
#     print(f"❌ Registration download failed: {reg_response.status_code}")

# STEP 3: Download Application Form
# app_response = session.get(application_form_url)
# if app_response.status_code == 200:
#     with open(f"application_form_{registration_number}.pdf", "wb") as f:
#         f.write(app_response.content)
#     print("✅ Application Form downloaded.")
# else:
#     print(f"❌ Application form download failed: {app_response.status_code}")

# STEP 4: Download Licence Certificate

for ids in registration_number:
    login_url = f"https://foscos.fssai.gov.in/gateway/fbo_readonly/getlogintofortacereg/{ids}"
    login_response = session.get(login_url)
    print("Step 1: Init session", login_response.status_code)
    licence_url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/license/{ids}/2"
    lice_response = session.get(licence_url)
    if lice_response.status_code == 200:
        with open(f"Licence_{ids}.pdf", "wb") as f:
            f.write(lice_response.content)
        print("Licence Certificate downloaded.")
    else:
        print(f"Licence download failed: {lice_response.status_code}")

