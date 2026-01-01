import requests
import json
import base64
import logging
from flask import current_app, render_template

logger = logging.getLogger(__name__)

def exchange_code_for_tokens(code):
    """Exchange authorization code for access tokens"""
    tenant_id = current_app.config.get('AZURE_TENANT_ID', '6ba231bb-ad9e-41b9-b23d-674c80196bbd')
    client_id = current_app.config.get('AZURE_CLIENT_ID', '11ddc0cd-e6fc-48b6-8832-de61800fb41e')
    client_secret = current_app.config.get('AZURE_CLIENT_SECRET', '')
    redirect_uri = current_app.config.get('REDIRECT_URI', 'http://localhost:5000/auth/callback')
    scope = current_app.config.get('AZURE_SCOPES', 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access')

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Prepare token request data
    token_data = {
        'client_id': client_id,
        'scope': scope,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    # Add client secret if available (for confidential clients)
    if client_secret:
        token_data['client_secret'] = client_secret
        logger.info("[TOKEN EXCHANGE] Using client secret authentication")
    else:
        logger.info("[TOKEN EXCHANGE] No client secret - public client flow")

    logger.debug(f"[TOKEN EXCHANGE] URL: {token_url}")
    logger.debug(f"[TOKEN EXCHANGE] Scope: {scope}")
    logger.debug(f"[TOKEN EXCHANGE] Redirect URI: {redirect_uri}")

    # Make token request
    response = requests.post(
        token_url,
        data=token_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    logger.debug(f"[TOKEN EXCHANGE] Response status: {response.status_code}")

    # Handle token exchange errors
    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = json.dumps(error_json, indent=2)
            logger.error(f"[TOKEN EXCHANGE] Error details: {error_detail}")
        except:
            logger.error(f"[TOKEN EXCHANGE] Error response: {error_detail}")

        raise Exception(f"Token exchange failed: {error_detail}")

    tokens = response.json()
    logger.info(f"[TOKEN EXCHANGE] Received tokens: {list(tokens.keys())}")

    return tokens

def render_auth_success_page(tokens):
    """Render success page that posts tokens back to parent window"""
    access_token = tokens.get('access_token', '')
    refresh_token = tokens.get('refresh_token', '')
    id_token = tokens.get('id_token', '')

    return render_template('auth_success.html',
                          access_token=access_token,
                          refresh_token=refresh_token,
                          id_token=id_token)

def render_auth_error_page(error, description):
    """Render error page that notifies parent window"""
    return render_template('auth_error.html', error=error, description=description)

def decode_id_token(id_token):
    """Decode ID token to get user info"""
    if not id_token:
        return {'displayName': 'Authenticated User', 'name': 'Authenticated User'}

    try:
        # Decode JWT payload (without verification for simplicity)
        payload = id_token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        return {
            'displayName': decoded.get('name', 'Authenticated User'),
            'name': decoded.get('name', 'Authenticated User'),
            'email': decoded.get('email', decoded.get('preferred_username', '')),
            'oid': decoded.get('oid', '')
        }
    except Exception as e:
        logger.error(f"[DECODE ID TOKEN] Could not decode ID token: {e}")
        return {'displayName': 'Authenticated User', 'name': 'Authenticated User'}