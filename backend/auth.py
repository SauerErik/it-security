from functools import wraps
from flask import request, jsonify, g
import os
from keycloak.keycloak_openid import KeycloakOpenID
from keycloak.keycloak_admin import KeycloakAdmin
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# OpenID Client (Frontend Login, Token Refresh, Userinfo)
# -----------------------------
keycloak_openid = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_SERVER_URL"),
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    realm_name=os.getenv("KEYCLOAK_REALM"),
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
)

# -----------------------------
# Admin Client (Service Account / Client Credentials)
# -----------------------------
server_url = os.getenv("KEYCLOAK_SERVER_URL")
realm_name = os.getenv("KEYCLOAK_REALM")
admin_client_id = os.getenv("KEYCLOAK_ADMIN_CLIENT_ID")
admin_client_secret = os.getenv("KEYCLOAK_ADMIN_CLIENT_SECRET")

# Step 1: Get full token dict from Keycloak
keycloak_openid_admin = KeycloakOpenID(
    server_url=server_url,
    client_id=admin_client_id,
    realm_name=realm_name,
    client_secret_key=admin_client_secret,
)
try:
    admin_token_dict = keycloak_openid_admin.token(grant_type="client_credentials")
    # Step 2: Initialize KeycloakAdmin with the full token
    keycloak_admin = KeycloakAdmin(
        server_url=server_url,
        realm_name=realm_name,
        token=admin_token_dict,  # Pass the full token dict!
        verify=True
    )
except Exception:
    admin_token_dict = None
    keycloak_admin = None

# -----------------------------
# Decorator for protected routes
# -----------------------------
def keycloak_protect(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        refresh_header = request.headers.get("X-Refresh-Token", None)

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        access_token = auth_header.split(" ")[1]
        g.access_token = access_token

        try:
            g.user = keycloak_openid.userinfo(access_token)
        except Exception as e:
            if refresh_header:
                try:
                    new_tokens = keycloak_openid.refresh_token(refresh_header)
                    g.access_token = new_tokens["access_token"]
                    g.user = keycloak_openid.userinfo(g.access_token)
                except Exception as e2:
                    return jsonify({"error": "Token invalid or expired", "details": str(e2)}), 401
            else:
                return jsonify({"error": "Token invalid or expired", "details": str(e)}), 401

        request.user = g.user
        return f(*args, **kwargs)
    return decorated

# -----------------------------
# Admin helper functions
# -----------------------------
def get_all_users():
    return keycloak_admin.get_users({})

def get_user_by_id(user_id):
    return keycloak_admin.get_user(user_id)

def get_user_by_username(username):
    user_id = keycloak_admin.get_user_id(username)
    if user_id:
        return keycloak_admin.get_user(user_id)
    return None

def create_user(payload, exist_ok=True):
    return keycloak_admin.create_user(payload, exist_ok=exist_ok)

def update_user(user_id, payload):
    return keycloak_admin.update_user(user_id, payload)

def delete_user(user_id):
    return keycloak_admin.delete_user(user_id)

def set_user_password(user_id, password, temporary=False):
    return keycloak_admin.set_user_password(user_id, password, temporary)
