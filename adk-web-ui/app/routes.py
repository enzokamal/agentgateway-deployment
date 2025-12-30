# from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
# from urllib.parse import urlencode
# import requests
# from .adk_client import list_sessions, create_session, get_session_events, send_message, delete_session

# bp = Blueprint("main", __name__)

# @bp.before_request
# def require_auth():
#     # Allow access to auth routes and login
#     if request.endpoint in ['main.login', 'main.auth_callback', 'main.auth_store_tokens', 'main.auth_manual_token']:
#         return
#     if not session.get('authenticated'):
#         return redirect(url_for('main.login'))

# @bp.route("/login")
# def login():
#     from urllib.parse import quote
#     # Make sure scope is properly formatted
#     scope = "api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access"
    
#     auth_url = (
#         "https://login.microsoftonline.com/6ba231bb-ad9e-41b9-b23d-674c80196bbd/oauth2/v2.0/authorize?"
#         + urlencode({
#             "client_id": "11ddc0cd-e6fc-48b6-8832-de61800fb41e",
#             "response_type": "code",
#             "redirect_uri": "http://localhost:5000/auth/callback",
#             "scope": scope,
#             "response_mode": "query",
#             "prompt": "select_account"
#         })
#     )
#     print(f"Generated auth URL: {auth_url}")
#     return render_template("login.html", auth_url=auth_url)

# @bp.route("/login", methods=["POST"])
# def login_post():
#     # Mock authentication for development
#     session['authenticated'] = True
#     session['user'] = {
#         'displayName': 'Test User',
#         'name': 'Test User'
#     }
#     return redirect(url_for('main.index'))

# @bp.route('/auth/callback')
# def auth_callback():
#     code = request.args.get('code')
#     error = request.args.get('error')
#     error_description = request.args.get('error_description')
#     print(f"Auth callback received: code={code}, error={error}, error_description={error_description}")

#     if error:
#         return f'''
#         <html>
#         <head><title>Authentication Error</title></head>
#         <body style="font-family: Arial, sans-serif; padding: 20px;">
#           <h2>Authentication Error</h2>
#           <p><strong>Error:</strong> {error}</p>
#           <p><strong>Description:</strong> {error_description or 'No description provided'}</p>
#           <script>
#             window.opener.postMessage({{ type: 'auth_error', error: '{error}', description: '{error_description or ""}' }}, '*');
#             window.close();
#           </script>
#         </body>
#         </html>
#         '''

#     if code:
#         try:
#             print(f"Client secret present: {bool(current_app.config['AZURE_CLIENT_SECRET'])}")
#             # Exchange code for tokens
#             token_url = f"https://login.microsoftonline.com/{current_app.config['AZURE_TENANT_ID']}/oauth2/v2.0/token"
#             data = {
#                 'client_id': current_app.config['AZURE_CLIENT_ID'],
#                 'client_secret': current_app.config['AZURE_CLIENT_SECRET'],
#                 'code': code,
#                 'grant_type': 'authorization_code',
#                 'redirect_uri': current_app.config['REDIRECT_URI'],
#                 'scope': current_app.config['AZURE_SCOPES'].replace('openid ', '')
#             }
#             print(f"Token exchange request: url={token_url}, data keys={list(data.keys())}, client_secret_set={bool(data['client_secret'])}, scope={data['scope']}, redirect_uri={data['redirect_uri']}")
#             response = requests.post(token_url, data=data)
#             print(f"Token exchange response status: {response.status_code}, headers: {dict(response.headers)}")
#             if response.status_code != 200:
#                 print(f"Token exchange failed: {response.text}")
#                 try:
#                     error_json = response.json()
#                     print(f"Error details: {error_json}")
#                 except:
#                     print("No JSON error details")
#             response.raise_for_status()
#             tokens = response.json()
#             print("Token exchange successful, tokens received")
#             print(f"Tokens keys: {list(tokens.keys())}")

#             return f'''
#             <html>
#             <head><title>Authentication Successful</title></head>
#             <body style="font-family: Arial, sans-serif; padding: 20px;">
#               <h2>Authentication Successful</h2>
#               <p>You will be redirected shortly...</p>
#               <script>
#                 window.opener.postMessage({{
#                   type: 'auth_success',
#                   access_token: '{tokens.get("access_token", "")}',
#                   refresh_token: '{tokens.get("refresh_token", "")}',
#                   id_token: '{tokens.get("id_token", "")}'
#                 }}, '*');
#                 window.close();
#               </script>
#             </body>
#             </html>
#             '''
#         except Exception as e:
#             print(f"Exception in token exchange: {str(e)}")
#             return f'''
#             <html>
#             <head><title>Authentication Error</title></head>
#             <body style="font-family: Arial, sans-serif; padding: 20px;">
#               <h2>Token Exchange Failed</h2>
#               <p>Failed to exchange authorization code for access token.</p>
#               <p>Error: {str(e)}</p>
#               <script>
#                 window.opener.postMessage({{
#                   type: 'auth_error',
#                   error: 'token_exchange_failed',
#                   description: '{str(e)}'
#                 }}, '*');
#                 window.close();
#               </script>
#             </body>
#             </html>
#             '''

#     return '''
#     <html>
#     <head><title>No Authorization Code</title></head>
#     <body style="font-family: Arial, sans-serif; padding: 20px;">
#       <h2>No Authorization Code</h2>
#       <p>No authorization code was received. Please try the authentication process again.</p>
#       <script>
#         window.opener.postMessage({ type: 'auth_error', error: 'no_code', description: 'No authorization code received' }, '*');
#         window.close();
#       </script>
#     </body>
#     </html>
#     '''

# @bp.route('/auth/store-tokens', methods=['POST'])
# def auth_store_tokens():
#     data = request.get_json()
#     access_token = data.get('access_token')
#     refresh_token = data.get('refresh_token')
#     id_token = data.get('id_token')

#     if not access_token:
#         return {'error': 'Access token is required'}, 400
#     print("Storing tokens in session")
#     print(f"Access token present: {bool(access_token)}, refresh: {bool(refresh_token)}, id: {bool(id_token)}")
#     session['authenticated'] = True
#     session['user'] = {
#         'displayName': 'Authenticated User',
#         'name': 'Authenticated User',
#         'accessToken': access_token,
#         'refreshToken': refresh_token,
#         'idToken': id_token
#     }

#     return {'success': True, 'message': 'Authentication successful'}

# @bp.route('/auth/manual-token', methods=['POST'])
# def auth_manual_token():
#     data = request.get_json()
#     token = data.get('token')

#     if not token:
#         return {'error': 'Token is required'}, 400

#     # Basic JWT check
#     if not token.count('.') == 2:
#         return {'error': 'Invalid token format'}, 400

#     session['authenticated'] = True
#     session['user'] = {
#         'displayName': 'Manual Token User',
#         'name': 'Manual Token User',
#         'accessToken': token
#     }

#     return {'success': True, 'message': 'Manual token authentication successful'}

# @bp.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('main.login'))

# @bp.route("/")
# def index():
#     print(f"Index route: authenticated={session.get('authenticated')}, user keys={list(session.get('user', {}).keys()) if session.get('user') else 'None'}")
#     if session.get('authenticated'):
#         sid = create_session(session['user']['accessToken'])
#         events = get_session_events(sid, session['user']['accessToken'])
#         return render_template("chat.html", sid=sid, events=events, user=session.get('user', {}))
#     else:
#         return redirect(url_for('main.login'))

# @bp.route("/session/new", methods=["POST"])
# def new_session_route():
#     sid = create_session(session['user']['accessToken'])
#     return redirect(url_for("main.chat", sid=sid))

# @bp.route("/session/<sid>")
# def chat(sid):
#     events = get_session_events(sid, session['user']['accessToken'])
#     return render_template("chat.html", sid=sid, events=events, user=session.get('user', {}))

# @bp.route("/session/<sid>/send", methods=["POST"])
# def send_message_route(sid):
#     user_message = request.form["message"]
#     send_message(sid, user_message, session['user']['accessToken'])
#     return redirect(url_for("main.chat", sid=sid))

# @bp.route("/session/<sid>/delete", methods=["POST"])
# def delete_session_route(sid):
#     delete_session(sid, session['user']['accessToken'])
#     return redirect(url_for("main.index"))


from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, jsonify
from urllib.parse import urlencode, quote
import requests
import base64
import json
from .adk_client import list_sessions, create_session, get_session_events, send_message, delete_session

bp = Blueprint("main", __name__)

@bp.before_request
def require_auth():
    """Middleware to check authentication before each request"""
    # Allow access to auth routes and static files without authentication
    public_endpoints = ['main.login', 'main.login_post', 'main.auth_callback', 
                       'main.auth_store_tokens', 'main.auth_manual_token', 'main.health', 
                       'static']
    
    # Skip auth check for static files and public endpoints
    if request.endpoint in public_endpoints or request.endpoint is None:
        return
    
    # Check if user is authenticated
    if not session.get('authenticated'):
        print(f"[AUTH CHECK] Unauthenticated access attempt to: {request.endpoint}")
        return redirect(url_for('main.login'))

@bp.route("/login")
def login():
    """Initiate Azure AD OAuth flow"""
    # Azure AD OAuth configuration
    tenant_id = current_app.config.get('AZURE_TENANT_ID', '6ba231bb-ad9e-41b9-b23d-674c80196bbd')
    client_id = current_app.config.get('AZURE_CLIENT_ID', '11ddc0cd-e6fc-48b6-8832-de61800fb41e')
    redirect_uri = current_app.config.get('REDIRECT_URI', 'http://localhost:5000/auth/callback')
    scope = current_app.config.get('AZURE_SCOPES', 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access')

    print(f"[AUTH] Scope: {scope}")
    print(f"[AUTH] Redirect URI: {redirect_uri}")

    return render_template("login.html", tenant_id=tenant_id, client_id=client_id, redirect_uri=redirect_uri, scope=scope)

@bp.route("/login", methods=["POST"])
def login_post():
    """Mock authentication for development/testing"""
    session['authenticated'] = True
    session['user'] = {
        'displayName': 'Test User',
        'name': 'Test User'
    }
    return redirect(url_for('main.index'))

@bp.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Azure AD"""
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    state = request.args.get('state')
    
    print(f"[AUTH CALLBACK] Code present: {bool(code)}, Error: {error}")
    
    # Handle OAuth errors
    if error:
        error_msg = error_description or 'No description provided'
        print(f"[AUTH CALLBACK] OAuth error: {error} - {error_msg}")
        return render_auth_error_page(error, error_msg)
    
    # Handle missing authorization code
    if not code:
        print("[AUTH CALLBACK] No authorization code received")
        return render_auth_error_page('no_code', 'No authorization code received')
    
    # Exchange authorization code for tokens
    try:
        tokens = exchange_code_for_tokens(code)
        print("[AUTH CALLBACK] Token exchange successful")
        return render_auth_success_page(tokens)
    except Exception as e:
        print(f"[AUTH CALLBACK] Token exchange failed: {str(e)}")
        return render_auth_error_page('token_exchange_failed', str(e))

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
        print("[TOKEN EXCHANGE] Using client secret authentication")
    else:
        print("[TOKEN EXCHANGE] No client secret - public client flow")
    
    print(f"[TOKEN EXCHANGE] URL: {token_url}")
    print(f"[TOKEN EXCHANGE] Scope: {scope}")
    print(f"[TOKEN EXCHANGE] Redirect URI: {redirect_uri}")
    
    # Make token request
    response = requests.post(
        token_url,
        data=token_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    print(f"[TOKEN EXCHANGE] Response status: {response.status_code}")
    
    # Handle token exchange errors
    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = json.dumps(error_json, indent=2)
            print(f"[TOKEN EXCHANGE] Error details: {error_detail}")
        except:
            print(f"[TOKEN EXCHANGE] Error response: {error_detail}")
        
        raise Exception(f"Token exchange failed: {error_detail}")
    
    tokens = response.json()
    print(f"[TOKEN EXCHANGE] Received tokens: {list(tokens.keys())}")
    
    return tokens

def render_auth_success_page(tokens):
    """Render success page that posts tokens back to parent window"""
    access_token = tokens.get('access_token', '')
    refresh_token = tokens.get('refresh_token', '')
    id_token = tokens.get('id_token', '')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
            }}
            .checkmark {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: block;
                stroke-width: 2;
                stroke: #4CAF50;
                stroke-miterlimit: 10;
                margin: 0 auto 20px;
                box-shadow: inset 0px 0px 0px #4CAF50;
                animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
            }}
            .checkmark__circle {{
                stroke-dasharray: 166;
                stroke-dashoffset: 166;
                stroke-width: 2;
                stroke-miterlimit: 10;
                stroke: #4CAF50;
                fill: none;
                animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
            }}
            .checkmark__check {{
                transform-origin: 50% 50%;
                stroke-dasharray: 48;
                stroke-dashoffset: 48;
                animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
            }}
            @keyframes stroke {{
                100% {{ stroke-dashoffset: 0; }}
            }}
            @keyframes scale {{
                0%, 100% {{ transform: none; }}
                50% {{ transform: scale3d(1.1, 1.1, 1); }}
            }}
            @keyframes fill {{
                100% {{ box-shadow: inset 0px 0px 0px 30px #4CAF50; }}
            }}
            h2 {{ color: #333; margin: 0 0 10px 0; }}
            p {{ color: #666; margin: 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
            <h2>Authentication Successful!</h2>
            <p>Redirecting you back to the application...</p>
        </div>
        <script>
            (function() {{
                try {{
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'auth_success',
                            access_token: '{access_token}',
                            refresh_token: '{refresh_token}',
                            id_token: '{id_token}'
                        }}, '*');
                        setTimeout(function() {{ window.close(); }}, 1500);
                    }} else {{
                        console.error('No opener window found');
                        setTimeout(function() {{ 
                            window.location.href = '/'; 
                        }}, 2000);
                    }}
                }} catch (e) {{
                    console.error('Error posting message:', e);
                    setTimeout(function() {{ window.location.href = '/'; }}, 2000);
                }}
            }})();
        </script>
    </body>
    </html>
    '''

def render_auth_error_page(error, description):
    """Render error page that notifies parent window"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Error</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 500px;
            }}
            .error-icon {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: #f44336;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 48px;
            }}
            h2 {{ color: #333; margin: 0 0 10px 0; }}
            .error-code {{ 
                color: #f44336; 
                font-weight: bold; 
                margin: 10px 0;
                font-family: monospace;
            }}
            .error-description {{ 
                color: #666; 
                margin: 10px 0;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 5px;
                word-wrap: break-word;
            }}
            .actions {{
                margin-top: 20px;
                text-align: center;
            }}
            button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">✕</div>
            <h2>Authentication Failed</h2>
            <div class="error-code">Error: {error}</div>
            <div class="error-description">{description}</div>
            <div class="actions">
                <button onclick="tryAgain()">Try Again</button>
            </div>
        </div>
        <script>
            function tryAgain() {{
                if (window.opener) {{
                    window.close();
                    window.opener.location.reload();
                }} else {{
                    window.location.href = '/login';
                }}
            }}
            
            (function() {{
                try {{
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'auth_error',
                            error: '{error}',
                            description: '{description}'
                        }}, '*');
                    }}
                }} catch (e) {{
                    console.error('Error posting message:', e);
                }}
            }})();
        </script>
    </body>
    </html>
    '''

@bp.route('/auth/store-tokens', methods=['POST'])
def auth_store_tokens():
    """Store OAuth tokens in session after successful authentication"""
    data = request.get_json()
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    id_token = data.get('id_token')
    
    if not access_token:
        print("[STORE TOKENS] Error: No access token provided")
        return jsonify({'error': 'Access token is required'}), 400
    
    # Decode ID token to get user info (if available)
    user_info = {'displayName': 'Authenticated User', 'name': 'Authenticated User'}
    if id_token:
        try:
            # Decode JWT payload (without verification for simplicity)
            payload = id_token.split('.')[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            user_info = {
                'displayName': decoded.get('name', 'Authenticated User'),
                'name': decoded.get('name', 'Authenticated User'),
                'email': decoded.get('email', decoded.get('preferred_username', '')),
                'oid': decoded.get('oid', '')
            }
            print(f"[STORE TOKENS] User info from ID token: {user_info['displayName']}")
        except Exception as e:
            print(f"[STORE TOKENS] Could not decode ID token: {e}")
    
    # Store in session
    session['authenticated'] = True
    session['user'] = {
        **user_info,
        'accessToken': access_token,
        'refreshToken': refresh_token,
        'idToken': id_token
    }
    
    print(f"[STORE TOKENS] Successfully stored tokens for user: {user_info['displayName']}")
    return jsonify({'success': True, 'message': 'Authentication successful'})

@bp.route('/auth/manual-token', methods=['POST'])
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
    user_info = {'displayName': 'Manual Token User', 'name': 'Manual Token User'}
    try:
        payload = token.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        user_info = {
            'displayName': decoded.get('name', 'Manual Token User'),
            'name': decoded.get('name', 'Manual Token User'),
            'email': decoded.get('email', decoded.get('preferred_username', ''))
        }
        print(f"[MANUAL TOKEN] Decoded user: {user_info['displayName']}")
    except Exception as e:
        print(f"[MANUAL TOKEN] Could not decode token: {e}")
    
    session['authenticated'] = True
    session['user'] = {
        **user_info,
        'accessToken': token
    }
    
    print("[MANUAL TOKEN] Manual token authentication successful")
    return jsonify({'success': True, 'message': 'Manual token authentication successful'})

@bp.route('/logout')
def logout():
    """Clear session and logout user"""
    user = session.get('user', {})
    print(f"[LOGOUT] User logged out: {user.get('displayName', 'Unknown')}")
    session.clear()
    return redirect(url_for('main.login'))

@bp.route("/")
def index():
    """Main application page - creates a new session and displays chat"""
    if not session.get('authenticated'):
        return redirect(url_for('main.login'))
    
    user = session.get('user', {})
    print(f"[INDEX] User accessing index: {user.get('displayName', 'Unknown')}")
    
    try:
        access_token = user.get('accessToken')
        if not access_token:
            print("[INDEX] Error: No access token in session")
            session.clear()
            return redirect(url_for('main.login'))
        
        sid = create_session(access_token)
        events = get_session_events(sid, access_token)
        
        return render_template("chat.html", sid=sid, events=events, user=user)
    except Exception as e:
        print(f"[INDEX] Error: {str(e)}")
        # If token is invalid or expired, redirect to login
        session.clear()
        return redirect(url_for('main.login'))

@bp.route("/session/new", methods=["POST"])
def new_session_route():
    """Create a new chat session"""
    access_token = session['user']['accessToken']
    sid = create_session(access_token)
    print(f"[NEW SESSION] Created session: {sid}")
    return redirect(url_for("main.chat", sid=sid))

@bp.route("/session/<sid>")
def chat(sid):
    """Display a specific chat session"""
    access_token = session['user']['accessToken']
    try:
        events = get_session_events(sid, access_token)
        return render_template("chat.html", sid=sid, events=events, user=session.get('user', {}))
    except Exception as e:
        print(f"[CHAT] Error loading session {sid}: {str(e)}")
        return redirect(url_for('main.index'))

@bp.route("/session/<sid>/send", methods=["POST"])
def send_message_route(sid):
    """Send a message in a chat session"""
    user_message = request.form.get("message", "")
    if not user_message.strip():
        return redirect(url_for("main.chat", sid=sid))
    
    access_token = session['user']['accessToken']
    try:
        send_message(sid, user_message, access_token)
        print(f"[SEND MESSAGE] Sent message to session {sid}")
    except Exception as e:
        print(f"[SEND MESSAGE] Error: {str(e)}")
    
    return redirect(url_for("main.chat", sid=sid))

@bp.route("/session/<sid>/delete", methods=["POST"])
def delete_session_route(sid):
    """Delete a chat session"""
    access_token = session['user']['accessToken']
    try:
        delete_session(sid, access_token)
        print(f"[DELETE SESSION] Deleted session: {sid}")
    except Exception as e:
        print(f"[DELETE SESSION] Error: {str(e)}")
    
    return redirect(url_for("main.index"))

# Health check endpoint
@bp.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'authenticated': session.get('authenticated', False)})

@bp.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404 errors"""
    return '', 204