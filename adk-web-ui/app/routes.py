from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from urllib.parse import urlencode
import requests
from .adk_client import list_sessions, create_session, get_session_events, send_message, delete_session

bp = Blueprint("main", __name__)

@bp.before_request
def require_auth():
    # Allow access to auth routes and login
    if request.endpoint in ['main.login', 'main.auth_callback', 'main.auth_store_tokens', 'main.auth_manual_token']:
        return
    if not session.get('authenticated'):
        return redirect(url_for('main.login'))

@bp.route("/login")
def login():
    from urllib.parse import quote
    auth_url = f"https://login.microsoftonline.com/{current_app.config['AZURE_TENANT_ID']}/oauth2/v2.0/authorize?" + urlencode({
        'client_id': current_app.config['AZURE_CLIENT_ID'],
        'response_type': 'code',
        'redirect_uri': current_app.config['REDIRECT_URI'],
        'scope': f'openid api://{current_app.config["AZURE_CLIENT_ID"]}/.default'
    })
    return render_template("login.html", auth_url=auth_url)

@bp.route("/login", methods=["POST"])
def login_post():
    # Mock authentication for development
    session['authenticated'] = True
    session['user'] = {
        'displayName': 'Test User',
        'name': 'Test User'
    }
    return redirect(url_for('main.index'))

@bp.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    if error:
        return f'''
        <html>
        <head><title>Authentication Error</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2>Authentication Error</h2>
          <p><strong>Error:</strong> {error}</p>
          <p><strong>Description:</strong> {error_description or 'No description provided'}</p>
          <script>
            window.opener.postMessage({{ type: 'auth_error', error: '{error}', description: '{error_description or ""}' }}, '*');
            window.close();
          </script>
        </body>
        </html>
        '''

    if code:
        try:
            # Exchange code for tokens
            token_url = f"https://login.microsoftonline.com/{current_app.config['AZURE_TENANT_ID']}/oauth2/v2.0/token"
            data = {
                'client_id': current_app.config['AZURE_CLIENT_ID'],
                'client_secret': current_app.config['AZURE_CLIENT_SECRET'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': current_app.config['REDIRECT_URI'],
                'scope': f'openid api://{current_app.config["AZURE_CLIENT_ID"]}/.default'
            }
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            tokens = response.json()

            return f'''
            <html>
            <head><title>Authentication Successful</title></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
              <h2>Authentication Successful</h2>
              <p>You will be redirected shortly...</p>
              <script>
                window.opener.postMessage({{
                  type: 'auth_success',
                  access_token: '{tokens.get("access_token", "")}',
                  refresh_token: '{tokens.get("refresh_token", "")}',
                  id_token: '{tokens.get("id_token", "")}'
                }}, '*');
                window.close();
              </script>
            </body>
            </html>
            '''
        except Exception as e:
            return f'''
            <html>
            <head><title>Authentication Error</title></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
              <h2>Token Exchange Failed</h2>
              <p>Failed to exchange authorization code for access token.</p>
              <p>Error: {str(e)}</p>
              <script>
                window.opener.postMessage({{
                  type: 'auth_error',
                  error: 'token_exchange_failed',
                  description: '{str(e)}'
                }}, '*');
                window.close();
              </script>
            </body>
            </html>
            '''

    return '''
    <html>
    <head><title>No Authorization Code</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
      <h2>No Authorization Code</h2>
      <p>No authorization code was received. Please try the authentication process again.</p>
      <script>
        window.opener.postMessage({ type: 'auth_error', error: 'no_code', description: 'No authorization code received' }, '*');
        window.close();
      </script>
    </body>
    </html>
    '''

@bp.route('/auth/store-tokens', methods=['POST'])
def auth_store_tokens():
    data = request.get_json()
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    id_token = data.get('id_token')

    if not access_token:
        return {'error': 'Access token is required'}, 400

    session['authenticated'] = True
    session['user'] = {
        'displayName': 'Authenticated User',
        'name': 'Authenticated User',
        'accessToken': access_token,
        'refreshToken': refresh_token,
        'idToken': id_token
    }

    return {'success': True, 'message': 'Authentication successful'}

@bp.route('/auth/manual-token', methods=['POST'])
def auth_manual_token():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return {'error': 'Token is required'}, 400

    # Basic JWT check
    if not token.count('.') == 2:
        return {'error': 'Invalid token format'}, 400

    session['authenticated'] = True
    session['user'] = {
        'displayName': 'Manual Token User',
        'name': 'Manual Token User',
        'accessToken': token
    }

    return {'success': True, 'message': 'Manual token authentication successful'}

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@bp.route("/")
def index():
    if session.get('authenticated'):
        sid = create_session(session['user']['accessToken'])
        events = get_session_events(sid, session['user']['accessToken'])
        return render_template("chat.html", sid=sid, events=events, user=session.get('user', {}))
    else:
        return redirect(url_for('main.login'))

@bp.route("/session/new", methods=["POST"])
def new_session_route():
    sid = create_session(session['user']['accessToken'])
    return redirect(url_for("main.chat", sid=sid))

@bp.route("/session/<sid>")
def chat(sid):
    events = get_session_events(sid, session['user']['accessToken'])
    return render_template("chat.html", sid=sid, events=events, user=session.get('user', {}))

@bp.route("/session/<sid>/send", methods=["POST"])
def send_message_route(sid):
    user_message = request.form["message"]
    send_message(sid, user_message, session['user']['accessToken'])
    return redirect(url_for("main.chat", sid=sid))

@bp.route("/session/<sid>/delete", methods=["POST"])
def delete_session_route(sid):
    delete_session(sid, session['user']['accessToken'])
    return redirect(url_for("main.index"))
