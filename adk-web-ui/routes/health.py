from flask import Blueprint, session, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'authenticated': session.get('authenticated', False)})