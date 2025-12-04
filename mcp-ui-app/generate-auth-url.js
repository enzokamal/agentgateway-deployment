#!/usr/bin/env node

// Script to generate Entra ID authorization URL for testing

const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || '11ddc0cd-e6fc-48b6-8832-de61800fb41e';
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || '6ba231bb-ad9e-41b9-b23d-674c80196bbd';
const REDIRECT_URI = process.env.REDIRECT_URI || 'http://localhost:3000/auth/callback';

const authUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/authorize?` +
  new URLSearchParams({
    client_id: AZURE_CLIENT_ID,
    response_type: 'code',
    redirect_uri: REDIRECT_URI,
    scope: 'api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/.default',
    response_mode: 'query'
  }).toString();

console.log('🔗 Entra ID Authorization URL:');
console.log('================================');
console.log(authUrl);
console.log('================================');
console.log('\n📋 Instructions:');
console.log('1. Copy and paste this URL into your browser');
console.log('2. Sign in with your Microsoft account');
console.log('3. After authentication, copy the "code" parameter from the redirect URL');
console.log('4. Paste the code into the MCP UI login form');
console.log('\n⚠️  Note: Make sure your redirect URI is configured in the Entra ID app registration');