from src.api.security.password import hash_password
from getpass import getpass

for role in ("ANALYST", "VIEWER"):
    password = getpass(f"Enter password for {role}: ")
    print(f"\n{role} password hash:")
    print(hash_password(password))
    print()