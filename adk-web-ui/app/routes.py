from flask import Blueprint, render_template, request, redirect, url_for
from .adk_client import list_sessions, create_session, get_session_events, send_message, delete_session

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    sessions = list_sessions()
    return render_template("index.html", sessions=sessions)

@bp.route("/session/new", methods=["POST"])
def new_session_route():
    sid = create_session()
    return redirect(url_for("main.chat", sid=sid))

@bp.route("/session/<sid>")
def chat(sid):
    events = get_session_events(sid)
    return render_template("chat.html", sid=sid, events=events)

@bp.route("/session/<sid>/send", methods=["POST"])
def send_message_route(sid):
    user_message = request.form["message"]
    send_message(sid, user_message)
    return redirect(url_for("main.chat", sid=sid))

@bp.route("/session/<sid>/delete", methods=["POST"])
def delete_session_route(sid):
    delete_session(sid)
    return redirect(url_for("main.index"))
