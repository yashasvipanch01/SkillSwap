from app.core.security import create_access_token, decode_access_token, hash_password, verify_password

hashed = hash_password("secret123")
print("hash starts with:", hashed[:7], "length:", len(hashed))
print("right password:", verify_password("secret123", hashed))
print("wrong password:", verify_password("wrong", hashed))

token = create_access_token(42)
print("token parts:", len(token.split(".")))
print("token says user id:", decode_access_token(token))
