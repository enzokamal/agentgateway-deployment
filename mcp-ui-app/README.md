# MCP UI Application

A web UI for the Agent Gateway that provides automatic Entra ID authentication and access to MCP servers.

## Features

- **Chat Interface**: Interactive chat with MCP servers using natural language
- **Real-time Communication**: WebSocket support for instant responses
- **MCP Protocol Support**: Full MCP (Model Context Protocol) client implementation
- **Multi-Server Support**: Chat with different MCP servers (Example, HubSpot, SQL)
- **Automatic Authentication**: Mock OAuth for testing (configurable for production)
- **Session Management**: Secure user sessions with chat history
- **Responsive UI**: Modern, clean web interface

## Prerequisites

- Node.js 18+
- Docker
- Docker Hub account

## Local Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set environment variables:
   ```bash
   export AZURE_CLIENT_ID="11ddc0cd-e6fc-48b6-8832-de61800fb41e"
   export AZURE_CLIENT_SECRET="your-client-secret"  # Optional for code exchange
   export AZURE_TENANT_ID="6ba231bb-ad9e-41b9-b23d-674c80196bbd"
   export GATEWAY_URL="http://localhost:8080"
   export REDIRECT_URI="http://localhost:3000/auth/callback"
   ```

3. Start the application:
   ```bash
   npm start
   ```

4. Open http://localhost:3000 in your browser

## Authentication Methods

### Method 1: Authorization Code Flow (Recommended)

1. **Generate Authorization URL:**
   ```bash
   node generate-auth-url.js
   ```

2. **Authenticate:**
   - Copy the generated URL and open it in a browser
   - Sign in with your Microsoft account
   - After authentication, you'll be redirected to a URL with a `code` parameter

3. **Exchange Code:**
   - Copy the `code` value from the redirect URL
   - Visit http://localhost:3000
   - Paste the code into the authorization code field
   - Click "Exchange Code for Tokens"

### Method 2: Mock Authentication (Development)

- Click "Mock Authentication (Development)" for testing without real Entra ID setup
- This bypasses authentication for development purposes

## Docker Build and Push

1. Build the Docker image:
   ```bash
   docker build -t mcp-ui:latest .
   ```

2. Tag the image for Docker Hub:
   ```bash
   docker tag mcp-ui:latest your-dockerhub-username/mcp-ui:latest
   ```

3. Push to Docker Hub:
   ```bash
   docker push your-dockerhub-username/mcp-ui:latest
   ```

## Environment Variables

- `AZURE_CLIENT_ID`: Your Entra ID application client ID
- `AZURE_CLIENT_SECRET`: Your Entra ID application client secret (for confidential client)
- `AZURE_TENANT_ID`: Your Entra ID tenant ID
- `GATEWAY_URL`: URL of the Agent Gateway (default: http://agentgateway.default.svc.cluster.local:8080)
- `REDIRECT_URI`: OAuth redirect URI (default: http://localhost:3000/auth/callback)
- `PORT`: Port to run the application on (default: 3000)

## Usage

1. **Access the UI**: Navigate to http://localhost:3000 (or your configured route)
2. **Authenticate**: Click "Sign in (Mock Authentication)" for testing
3. **Explore Servers**: View available MCP servers on the left panel
4. **Test Connections**: Click "Test Connection" to verify server connectivity
5. **Start Chatting**: Click "Chat with Server" on any MCP server
6. **Ask Questions**: Type natural language questions in the chat interface
7. **Real-time Responses**: Get instant responses from MCP servers via WebSocket

### Chat Features

- **Natural Language Queries**: Ask questions like "What tools do you have?" or "Show me customer data"
- **Multi-Server Support**: Switch between different MCP servers during conversation
- **Real-time Updates**: See typing indicators and instant responses
- **Session Persistence**: Chat history maintained during your session

## API Endpoints

- `GET /`: Login page or dashboard
- `GET /login`: Initiate OAuth flow
- `GET /auth/callback`: OAuth callback
- `GET /logout`: Logout
- `GET /api/mcp/:server`: Proxy GET requests to MCP servers
- `POST /api/mcp/:server`: Proxy POST requests to MCP servers