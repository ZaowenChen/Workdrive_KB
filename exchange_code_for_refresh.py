import sys
import json
import requests

# === Fill these with your values (US DC) ===
CLIENT_ID     = "1000.KFXOPLNQX9KU4ZCULL5OCMXN5B62NI"
CLIENT_SECRET = "6314ad7501750547979b1a713ee270e9760a1d428d"
AUTH_CODE     = "1000.25a0dd10447666cc8dbfaee87290a6d3.104c0ee7a2ddc00fcaaaacc5ead8a774"

ACCOUNTS_BASE = "https://accounts.zoho.com"  # US data center

def main():
    url = f"{ACCOUNTS_BASE}/oauth/v2/token"
    data = {
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          AUTH_CODE,
        # For Self Client, redirect_uri is optional. If you registered one, add it:
        # "redirect_uri": "https://example.com/callback"
    }

    try:
        resp = requests.post(url, data=data, timeout=30)
    except Exception as e:
        print(f"Network error calling Zoho Accounts: {e}", file=sys.stderr)
        sys.exit(1)

    # Show raw response if non-2xx or missing fields
    try:
        payload = resp.json()
    except Exception:
        print(f"Non-JSON response ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"HTTP {resp.status_code} from Zoho: {json.dumps(payload, indent=2)}", file=sys.stderr)
        sys.exit(1)

    # Expect both access_token and refresh_token on success
    refresh = payload.get("refresh_token")
    access  = payload.get("access_token")

    if not refresh:
        # Common cause: using an expired/previously-used authorization code
        print("Zoho did not return a refresh_token.\n"
              f"Response was:\n{json.dumps(payload, indent=2)}", file=sys.stderr)
        sys.exit(2)

    print("✅ Success! Save this refresh token securely:")
    print(f'refresh_token="{refresh}"')
    if access:
        print("\n(For reference) short-lived access_token:")
        print(f'access_token="{access}"')
    else:
        print("\nNote: No access_token in response; you can mint one any time using the refresh_token.")

if __name__ == "__main__":
    main()
