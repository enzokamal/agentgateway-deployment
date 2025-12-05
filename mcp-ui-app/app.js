const express = require('express');
const session = require('express-session');
const axios = require('axios');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const requestId = uuidv4();

const app = express();
const port = process.env.PORT || 3000;

// Environment variables
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || '6ba231bb-ad9e-41b9-b23d-674c80196bbd';
const GATEWAY_URL = process.env.GATEWAY_URL || 'http://40.90.239.128:8000';
const REDIRECT_URI = process.env.REDIRECT_URI || 'http://40.90.239.128:3000/auth/callback';

// Mock user for local testing
const mockUser = {
  displayName: 'Test User',
  name: 'Test User',
  accessToken: null // Will be set dynamically
};

// Function to get access token using client credentials
async function getAccessToken() {
  const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
  const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || '';
  const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || '6ba231bb-ad9e-41b9-b23d-674c80196bbd';

  if (!AZURE_CLIENT_SECRET) {
    console.warn('AZURE_CLIENT_SECRET not set, using mock token for development');
    return 'mock-jwt-token-for-testing';
  }

  try {
    const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
    const params = new URLSearchParams({
      client_id: AZURE_CLIENT_ID,
      client_secret: AZURE_CLIENT_SECRET,
      scope: 'api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/.default',
      grant_type: 'client_credentials'
    });

    const response = await axios.post(tokenUrl, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    return response.data.access_token;
  } catch (error) {
    console.error('Failed to get access token:', error.response?.data || error.message);
    // Fallback to mock token for development
    return 'mock-jwt-token-for-testing';
  }
}


// MCP Protocol Client
class MCPClient {
  constructor(gatewayUrl, accessToken) {
    this.gatewayUrl = gatewayUrl;
    this.accessToken = accessToken;
    this.sessionId = null; // Initialize sessionId to null
  }

  async initialize(server = 'mcp-example') {
    try {
      const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: {
            name: 'mcp-ui-client',
            version: '1.0.0'
          }
        }
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
          'MCP-Protocol-Version': '2024-11-05',
          'Accept': 'application/json,text/event-stream'
        }
      });

      // CRITICAL: Use the session ID returned by the server
      if (response.data.result?.sessionId) {
        this.sessionId = response.data.result.sessionId;
        console.log('MCP Session initialized with server sessionId:', this.sessionId);
      } else {
        console.warn('No sessionId returned by server, using client-generated sessionId:', this.sessionId);
      }
      return response.data;
    } catch (error) {
      console.error('MCP Initialize error:', error.response?.data || error.message);
      throw error;
    }
  }

  async listTools(server = 'mcp-example') {
    try {
      const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
        jsonrpc: '2.0',
        id: this.sessionId,
        method: 'tools/list',
        params: {}
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
          'MCP-Protocol-Version': '2024-11-05',
          'Accept': 'application/json,text/event-stream',
          'MCP-Session-Id': this.sessionId
        }
      });

      return response.data;
    } catch (error) {
      console.error('MCP List Tools error:', error.response?.data || error.message);
      throw error;
    }
  }

  async callTool(server = 'mcp-example', toolName, args = {}) {
    try {
      console.log("session id:", this.sessionId)
      const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
        jsonrpc: '2.0',
        id: this.sessionId,
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        }
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json,text/event-stream',
          'MCP-Protocol-Version': '2024-11-05',
          'MCP-Session-Id': this.sessionId
        }
      });
      

      return response.data;
    } catch (error) {
      console.error('MCP Call Tool error:', error.response?.data || error.message);
      // console.log("Error from call tool function", error)
      throw error;
    }
  }

  async chat(server = 'mcp-example', message) {
    // Try different tools in order of preference
    const toolsToTry = ['query', 'chat', 'search'];

    for (const toolName of toolsToTry) {
      try {
        const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
          jsonrpc: '2.0',
          id: this.sessionId,
          method: 'tools/call',
          params: {
            name: toolName,
            arguments: toolName === 'query' ? { question: message } : { message: message }
          }
        }, {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
            'MCP-Protocol-Version': '2024-11-05',
            'Accept': 'application/json,text/event-stream',
            'MCP-Session-Id': this.sessionId
          }
        });

        return response.data;
      } catch (error) {
        console.warn(`Tool '${toolName}' failed:`, error.response?.status || error.message);
        // Continue to next tool
      }
    }

    // If all tools failed, throw an error
    throw new Error('No suitable chat tool available on the MCP server');
  }
}

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: false
}));
app.set('view engine', 'ejs');

// Routes
app.get('/auth/callback', async (req, res) => {
  const { code, error, error_description } = req.query;

  if (error) {
    return res.send(`
      <html>
        <head><title>Authentication Error</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2>Authentication Error</h2>
          <p><strong>Error:</strong> ${error}</p>
          <p><strong>Description:</strong> ${error_description || 'No description provided'}</p>
          <script>
            window.opener.postMessage({ type: 'auth_error', error: '${error}', description: '${error_description || ''}' }, '*');
            window.close();
          </script>
        </body>
      </html>
    `);
  }

  if (code) {
    try {
      // Automatically exchange the code for tokens
      const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
      const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || '';
      const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || '6ba231bb-ad9e-41b9-b23d-674c80196bbd';
      const REDIRECT_URI = process.env.REDIRECT_URI || 'http://40.90.239.128:3000/auth/callback';

      if (!AZURE_CLIENT_SECRET) {
        throw new Error('Azure client secret not configured');
      }

      const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
      const params = new URLSearchParams({
        client_id: AZURE_CLIENT_ID,
        client_secret: AZURE_CLIENT_SECRET,
        code: code,
        grant_type: 'authorization_code',
        redirect_uri: REDIRECT_URI,
        scope: 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/.default'
      });

      const response = await axios.post(tokenUrl, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      // Store tokens in session (this won't work in popup, need to pass to parent)
      // Instead, we'll send the tokens to the parent window

      return res.send(`
        <html>
          <head><title>Authentication Successful</title></head>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Authentication Successful</h2>
            <p>You will be redirected shortly...</p>
            <script>
              // Send tokens to parent window
              window.opener.postMessage({
                type: 'auth_success',
                access_token: '${response.data.access_token}',
                refresh_token: '${response.data.refresh_token || ''}',
                id_token: '${response.data.id_token || ''}'
              }, '*');
              window.close();
            </script>
          </body>
        </html>
      `);

    } catch (error) {
      console.error('Token exchange error in callback:', error.response?.data || error.message);
      return res.send(`
        <html>
          <head><title>Authentication Error</title></head>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Token Exchange Failed</h2>
            <p>Failed to exchange authorization code for access token.</p>
            <p>Error: ${error.response?.data?.error_description || error.message}</p>
            <script>
              window.opener.postMessage({
                type: 'auth_error',
                error: 'token_exchange_failed',
                description: '${error.response?.data?.error_description || error.message}'
              }, '*');
              window.close();
            </script>
          </body>
        </html>
      `);
    }
  }

  res.send(`
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
  `);
});

app.post('/auth/store-tokens', (req, res) => {
  const { access_token, refresh_token, id_token } = req.body;

  if (!access_token) {
    return res.status(400).json({ error: 'Access token is required' });
  }

  // Store tokens in session
  req.session.authenticated = true;
  req.session.user = {
    displayName: 'Authenticated User',
    name: 'Authenticated User',
    accessToken: access_token,
    refreshToken: refresh_token,
    idToken: id_token
  };

  res.json({ success: true, message: 'Authentication successful' });
});

app.post('/auth/manual-token', (req, res) => {
  const { token } = req.body;

  if (!token) {
    return res.status(400).json({ error: 'Token is required' });
  }

  // Validate that it's a JWT token (basic check)
  if (!token.includes('.') || token.split('.').length !== 3) {
    return res.status(400).json({ error: 'Invalid token format' });
  }

  // Store token in session
  req.session.authenticated = true;
  req.session.user = {
    displayName: 'Manual Token User',
    name: 'Manual Token User',
    accessToken: token,
    refreshToken: null,
    idToken: null
  };

  res.json({ success: true, message: 'Manual token authentication successful' });
});

app.get('/', (req, res) => {
  if (req.session.authenticated) {
    res.render('dashboard', { user: mockUser });
  } else {
    res.render('login', {
      AZURE_CLIENT_ID: AZURE_CLIENT_ID,
      AZURE_TENANT_ID: AZURE_TENANT_ID,
      REDIRECT_URI: REDIRECT_URI
    });
  }
});

app.post('/login', (req, res) => {
  // Mock authentication for local testing
  req.session.authenticated = true;
  req.session.user = mockUser;
  res.redirect('/');
});

app.post('/auth/exchange-code', async (req, res) => {
  const { code } = req.body;

  if (!code) {
    return res.status(400).json({ error: 'Authorization code is required' });
  }

  const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
  const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;
  const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || '6ba231bb-ad9e-41b9-b23d-674c80196bbd';
  const REDIRECT_URI = process.env.REDIRECT_URI || 'http://40.90.239.128:3000/auth/callback';

  if (!AZURE_CLIENT_SECRET) {
    return res.status(500).json({ error: 'Azure client secret not configured' });
  }

  try {
    const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
    const params = new URLSearchParams({
      client_id: AZURE_CLIENT_ID,
      client_secret: AZURE_CLIENT_SECRET,
      code: code,
      grant_type: 'authorization_code',
      redirect_uri: REDIRECT_URI,
      scope: 'api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/.default'
    });

    const response = await axios.post(tokenUrl, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    // Store tokens in session
    req.session.authenticated = true;
    req.session.user = {
      displayName: 'Authenticated User',
      name: 'Authenticated User',
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token
    };

    res.json({ success: true, message: 'Authentication successful' });

  } catch (error) {
    console.error('Token exchange error:', error.response?.data || error.message);
    res.status(500).json({
      error: 'Failed to exchange authorization code',
      details: error.response?.data?.error_description || error.message
    });
  }
});

app.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');

});

// Initialize MCP client for session
app.use('/api', async (req, res, next) => {
  if (req.session.authenticated && req.session.user) {
    // Use stored access token from session (from authorization code exchange)
    const accessToken = req.session.user.accessToken;
    if (accessToken) {
      req.mcpClient = new MCPClient(GATEWAY_URL, accessToken);
    } else {
      // Fallback: get fresh token using client credentials
      const freshToken = await getAccessToken();
      req.mcpClient = new MCPClient(GATEWAY_URL, freshToken);
    }
  }
  next();
});

// API routes to proxy to gateway
app.get('/api/mcp/:server', async (req, res) => {
  if (!req.session.authenticated) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  const accessToken = req.session.user?.accessToken;
  if (!accessToken) {
    return res.status(401).json({ error: 'No access token available' });
  }

  try {
    const response = await axios.get(`${GATEWAY_URL}/mcp/${req.params.server}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        // 'Accept': 'application/json'
        'Accept': 'application/json,text/event-stream',
        'MCP-Protocol-Version': '2024-11-05'
        // Note: These proxy routes don't maintain session state
      }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

app.post('/api/mcp/:server', async (req, res) => {
  if (!req.session.authenticated) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  const accessToken = req.session.user?.accessToken;
  if (!accessToken) {
    return res.status(401).json({ error: 'No access token available' });
  }

  try {
    const response = await axios.post(`${GATEWAY_URL}/mcp/${req.params.server}`, req.body, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        // 'Accept': 'application/json'
        'Accept': 'application/json,text/event-stream',
        'MCP-Protocol-Version': '2024-11-05'
        // Note: These proxy routes don't maintain session state
      }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

// Chat API endpoints
app.post('/api/chat/initialize', async (req, res) => {
  if (!req.session.authenticated) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  const { server = 'mcp-example' } = req.body;

  try {
    const result = await req.mcpClient.initialize(server);
    console.log("Using server-assigned session:", req.mcpClient.sessionId);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/chat/tools', async (req, res) => {
  if (!req.session.authenticated) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  const server = req.query.server || 'mcp-example';

  try {
    const result = await req.mcpClient.listTools(server);
    res.json({ success: true, tools: result.result?.tools || [] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chat/message', async (req, res) => {
  if (!req.session.authenticated) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  const { message, server = 'mcp-example' } = req.body;

  if (!message) {
    return res.status(400).json({ error: 'Message is required' });
  }

  try {
    const result = await req.mcpClient.chat(server, message);
    res.json({
      success: true,
      response: result.result?.content || result.result || 'No response'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// WebSocket server for real-time chat
const wss = new WebSocket.Server({ noServer: true });

wss.on('connection', async (ws, req) => {
  console.log('WebSocket client connected');

  // Get access token for this WebSocket connection
  let accessToken = mockUser.accessToken; // Default fallback

  // Try to get fresh token
  try {
    const freshToken = await getAccessToken();
    accessToken = freshToken;
  } catch (tokenError) {
    console.warn('Using fallback token for WebSocket:', tokenError.message);
  }

  const mcpClient = new MCPClient(GATEWAY_URL, accessToken);
  ws.mcpClient = mcpClient;

  ws.on('message', async (data) => {
    try {
      const message = JSON.parse(data.toString());
      const { type, payload } = message;

      if (type === 'chat') {
        const { message: chatMessage, server = 'mcp-example' } = payload;

        try {
          // Initialize if not done
          if (!ws.mcpClient.sessionId) {
            await ws.mcpClient.initialize(server);
          }

          // Send typing indicator
          ws.send(JSON.stringify({ type: 'typing', payload: { status: true } }));

          // Get response from MCP
          const result = await ws.mcpClient.chat(server, chatMessage);

          // Send response
          ws.send(JSON.stringify({
            type: 'response',
            payload: {
              message: result.result?.content || result.result || 'No response',
              server: server
            }
          }));

        } catch (error) {
          ws.send(JSON.stringify({
            type: 'error',
            payload: { message: error.message }
          }));
        } finally {
          ws.send(JSON.stringify({ type: 'typing', payload: { status: false } }));
        }
      }
    } catch (error) {
      ws.send(JSON.stringify({
        type: 'error',
        payload: { message: 'Invalid message format' }
      }));
    }
  });

  ws.on('close', () => {
    console.log('WebSocket client disconnected');
  });
});

const server = app.listen(port, () => {
  console.log(`MCP UI app listening at http://40.90.239.128:${port}`);
});

// Handle WebSocket upgrade
server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});