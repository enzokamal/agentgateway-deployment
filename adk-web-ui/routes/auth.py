from flask import Blueprint, session, request, redirect, url_for, jsonify, current_app, render_template
import logging
from auth.helpers import exchange_code_for_tokens, render_auth_success_page, render_auth_error_page, decode_id_token

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Initiate Azure AD OAuth flow"""
    tenant_id = current_app.config.get('AZURE_TENANT_ID')
    client_id = current_app.config.get('AZURE_CLIENT_ID')
    redirect_uri = current_app.config.get('REDIRECT_URI')
    scope = current_app.config.get('AZURE_SCOPES')

    return render_template("login.html", tenant_id=tenant_id, client_id=client_id, redirect_uri=redirect_uri, scope=scope)

@auth_bp.route("/login", methods=["POST"])
def login_post():
    """Mock authentication for development/testing"""
    session['authenticated'] = True
    session['user'] = {
        'displayName': 'Test User',
        'name': 'Test User'
    }
    return redirect(url_for('chat.index'))

@auth_bp.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Azure AD"""
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    state = request.args.get('state')

    logger.info(f"[AUTH CALLBACK] Code present: {bool(code)}, Error: {error}")

    # Handle OAuth errors
    if error:
        error_msg = error_description or 'No description provided'
        logger.error(f"[AUTH CALLBACK] OAuth error: {error} - {error_msg}")
        return render_auth_error_page(error, error_msg)

    # Handle missing authorization code
    if not code:
        logger.error("[AUTH CALLBACK] No authorization code received")
        return render_auth_error_page('no_code', 'No authorization code received')

    # Exchange authorization code for tokens
    try:
        tokens = exchange_code_for_tokens(code)
        logger.info("[AUTH CALLBACK] Token exchange successful")
        return render_auth_success_page(tokens)
    except Exception as e:
        logger.error(f"[AUTH CALLBACK] Token exchange failed: {str(e)}")
        return render_auth_error_page('token_exchange_failed', str(e))

@auth_bp.route('/auth/store-tokens', methods=['POST'])
def auth_store_tokens():
    """Store OAuth tokens in session after successful authentication"""
    data = request.get_json()
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    id_token = data.get('id_token')

    if not access_token:
        logger.error("[STORE TOKENS] Error: No access token provided")
        return jsonify({'error': 'Access token is required'}), 400

    # Decode ID token to get user info (if available)
    user_info = decode_id_token(id_token)

    # Store in session
    session['authenticated'] = True
    session['user'] = {
        **user_info,
        'accessToken': access_token,
        'refreshToken': refresh_token,
        'idToken': id_token
    }

    logger.info(f"[STORE TOKENS] Successfully stored tokens for user: {user_info['displayName']}")
    return jsonify({'success': True, 'message': 'Authentication successful'})

@auth_bp.route('/auth/manual-token', methods=['POST'])
def auth_manual_token():
    """Manually provide a token for testing purposes"""
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({'error': 'Token is required'}), 400

    # Basic JWT format validation
    if token.count('.') != 2:
        return jsonify({'error': 'Invalid token format. Must be a valid JWT.'}), 400

    # Try to decode token to get user info
    user_info = decode_id_token(token)

    session['authenticated'] = True
    session['user'] = {
        **user_info,
        'accessToken': token
    }

    logger.info("[MANUAL TOKEN] Manual token authentication successful")
    return jsonify({'success': True, 'message': 'Manual token authentication successful'})

@auth_bp.route('/logout')
def logout():
    """Clear session and logout user"""
    user = session.get('user', {})
    logger.info(f"[LOGOUT] User logged out: {user.get('displayName', 'Unknown')}")
    session.clear()
    return redirect(url_for('auth.login'))