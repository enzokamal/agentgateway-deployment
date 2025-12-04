const express = require('express');
const session = require('express-session');
const axios = require('axios');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const app = express();
const port = process.env.PORT || 3000;

// Environment variables
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || '6ba231bb-ad9e-41b9-b23d-674c80196bbd';
const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8080';
const REDIRECT_URI = process.env.REDIRECT_URI || 'http://localhost:3000/auth/callback';

// Mock user for local testing
const mockUser = {
  displayName: 'Test User',
  name: 'Test User',
  accessToken: null // Will be set dynamically
};

// Function to get access token using client credentials
async function getAccessToken() {
  const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
  const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;
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
    this.sessionId = null;
  }

  async initialize(server = 'mcp-example') {
    try {
      const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
        jsonrpc: '2.0',
        id: uuidv4(),
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {
            tools: {}
          },
          clientInfo: {
            name: 'mcp-ui-client',
            version: '1.0.0'
          }
        }
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      this.sessionId = response.data.result?.sessionId;
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
        id: uuidv4(),
        method: 'tools/list',
        params: {}
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
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
      const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
        jsonrpc: '2.0',
        id: uuidv4(),
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        }
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      return response.data;
    } catch (error) {
      console.error('MCP Call Tool error:', error.response?.data || error.message);
      throw error;
    }
  }

  async chat(server = 'mcp-example', message) {
    try {
      // For chat, we'll use a generic tool call or resources
      // This is a simplified implementation - in reality you'd have specific chat tools
      const response = await axios.post(`${this.gatewayUrl}/mcp/${server}`, {
        jsonrpc: '2.0',
        id: uuidv4(),
        method: 'tools/call',
        params: {
          name: 'chat',
          arguments: {
            message: message,
            session_id: this.sessionId
          }
        }
      }, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      return response.data;
    } catch (error) {
      // Fallback: try to use a generic query tool
      try {
        return await this.callTool(server, 'query', { question: message });
      } catch (fallbackError) {
        console.error('MCP Chat fallback error:', fallbackError.message);
        throw error;
      }
    }
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
app.get('/auth/callback', (req, res) => {
  const { code, error, error_description } = req.query;

  if (error) {
    return res.send(`
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2>Authentication Error</h2>
          <p><strong>Error:</strong> ${error}</p>
          <p><strong>Description:</strong> ${error_description || 'No description provided'}</p>
          <p><a href="/">← Back to Login</a></p>
        </body>
      </html>
    `);
  }

  if (code) {
    return res.send(`
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2>Authorization Code Received</h2>
          <p>Copy this authorization code and paste it in the login form:</p>
          <textarea readonly style="width: 100%; height: 100px; padding: 10px; font-family: monospace; font-size: 14px;">${code}</textarea>
          <br><br>
          <button onclick="copyToClipboard()" style="padding: 10px 20px; background: #0078d4; color: white; border: none; border-radius: 4px; cursor: pointer;">Copy to Clipboard</button>
          <br><br>
          <p><a href="/">← Back to Login</a></p>
          <script>
            function copyToClipboard() {
              const textarea = document.querySelector('textarea');
              textarea.select();
              document.execCommand('copy');
              alert('Code copied to clipboard!');
            }
          </script>
        </body>
      </html>
    `);
  }

  res.send(`
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>No Authorization Code</h2>
        <p>No authorization code was received. Please try the authentication process again.</p>
        <p><a href="/">← Back to Login</a></p>
      </body>
    </html>
  `);
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
  const REDIRECT_URI = process.env.REDIRECT_URI || 'http://localhost:3000/auth/callback';

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
      scope: 'openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/.default'
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

  try {
    const response = await axios.get(`${GATEWAY_URL}/mcp/${req.params.server}`, {
      headers: {
        'Authorization': `Bearer ${mockUser.accessToken}`,
        'Content-Type': 'application/json'
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

  try {
    const response = await axios.post(`${GATEWAY_URL}/mcp/${req.params.server}`, req.body, {
      headers: {
        'Authorization': `Bearer ${mockUser.accessToken}`,
        'Content-Type': 'application/json'
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

wss.on('connection', (ws, req) => {
  console.log('WebSocket client connected');

  ws.on('message', async (data) => {
    try {
      const message = JSON.parse(data.toString());
      const { type, payload } = message;

      if (type === 'chat') {
        const { message: chatMessage, server = 'mcp-example' } = payload;

        try {
          // Use stored access token from session for WebSocket connection
          let accessToken = mockUser.accessToken; // Default fallback

          // Try to get token from session if available
          // Note: WebSocket connections don't have direct access to session
          // In production, you'd need to pass the token in the WebSocket connection
          try {
            const freshToken = await getAccessToken();
            accessToken = freshToken;
          } catch (tokenError) {
            console.warn('Using fallback token for WebSocket:', tokenError.message);
          }

          // Create MCP client for this WebSocket connection
          const mcpClient = new MCPClient(GATEWAY_URL, accessToken);

          // Initialize if not done
          if (!mcpClient.sessionId) {
            await mcpClient.initialize(server);
          }

          // Send typing indicator
          ws.send(JSON.stringify({ type: 'typing', payload: { status: true } }));

          // Get response from MCP
          const result = await mcpClient.chat(server, chatMessage);

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
  console.log(`MCP UI app listening at http://localhost:${port}`);
});

// Handle WebSocket upgrade
server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});