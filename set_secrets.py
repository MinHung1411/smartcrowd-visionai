import requests
from nacl import encoding, public
import base64
import sys

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

token = "YOUR_GITHUB_TOKEN"
repo = "dovanminh1001/visionai-databricks"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# 1. Get public key for repo
url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
rsp = requests.get(url, headers=headers)
if rsp.status_code != 200:
    print(f"Failed to get public key: {rsp.text}")
    sys.exit(1)

data = rsp.json()
key_id = data["key_id"]
public_key = data["key"]

secrets = {
    "DATABRICKS_HOST": "https://adb-2751918341123456.7.azuredatabricks.net",
    "DATABRICKS_TOKEN": "YOUR_DATABRICKS_TOKEN"
}

for secret_name, secret_value in secrets.items():
    encrypted_value = encrypt(public_key, secret_value)
    put_url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    put_rsp = requests.put(put_url, headers=headers, json=payload)
    if put_rsp.status_code in (201, 204):
        print(f"Successfully set {secret_name}")
    else:
        print(f"Failed to set {secret_name}: {put_rsp.text}")

