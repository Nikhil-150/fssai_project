import requests

# ✅ Just change this value each time
registration_number = "116574560"

url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{registration_number}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://foscos.fssai.gov.in/",
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIyMDUyMTAzMTAwMDc5NSBmb3Njb3MuZnNzYWkuZ292LmluIDEwMy4yNDcuNi4xMzYgIiwiYXV0aG9yaXRpZXMiOlsiUk9MRV9GQk8iXSwidXNlcklkIjoiNjkzNjE5NTEiLCJpYXQiOjE3NTI4NDMwNDQsImV4cCI6MTc1MjkyOTQ0NH0.xoiqQrgW9Z6nSXoWKPN5lls_vsAK8urcX-XWVEB1VDgm2FUjh7FDQiIP8unmDsAu5E_R4kqcmGb2S6aBVMPT1g",
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
    "_ga_E101FG0RXN": "GS2.3.s1752845136$o2$g0$t1752845136$j60$l0$h0",
    f"key_{registration_number}": "ZFPF3b4Rwihz9PiHWxvfJ8ou2rb8NjE8rGW9nMy/hmA=",
    "_ga_X6L29149T6": "GS2.3.s1752841503$o1$g1$t1752842990$j19$l0$h0",
    "_gat": "1"
}

response = requests.get(url, headers=headers, cookies=cookies)

if response.status_code == 200:
    with open(f"fssai_registration_{registration_number}.pdf", "wb") as f:
        f.write(response.content)
    print(f"✅ PDF for registration {registration_number} downloaded successfully.")
else:
    print(f"❌ Failed to download for {registration_number}. Status code: {response.status_code}")
    print(response.text)
