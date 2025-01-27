import os

credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if credentials_path:
    print(f"Credentials file found: {credentials_path}")
else:
    print("GOOGLE_APPLICATION_CREDENTIALS not set!")
