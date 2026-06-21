"""
Web Server for Wumpus World Game GUI
======================================
Flask-based web server with level support.
"""

from flask import Flask, jsonify, request, send_from_directory
from game_engine import WumpusGame, LEVELS

app = Flask(__name__, static_folder="static", static_url_path="/static")
game = WumpusGame(level=1)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(game.get_state())


@app.route("/api/levels", methods=["GET"])
def get_levels():
    """Return all available levels."""
    return jsonify(LEVELS)


@app.route("/api/move", methods=["POST"])
def move():
    data = request.json
    return jsonify(game.move(data.get("direction", "right")))


@app.route("/api/shoot", methods=["POST"])
def shoot():
    data = request.json
    return jsonify(game.shoot(data.get("direction", "right")))


@app.route("/api/grab", methods=["POST"])
def grab():
    return jsonify(game.grab())


@app.route("/api/climb", methods=["POST"])
def climb():
    return jsonify(game.climb())


@app.route("/api/auto", methods=["POST"])
def auto_step():
    return jsonify(game.auto_step())


@app.route("/api/reset", methods=["POST"])
def reset():
    game.reset()
    return jsonify(game.get_state())


@app.route("/api/new_game", methods=["POST"])
def new_game():
    global game
    data = request.json or {}
    level = data.get("level", 1)
    game = WumpusGame(level=level)
    return jsonify(game.get_state())


if __name__ == "__main__":
    print("=" * 50)
    print("  Wumpus World Game Server")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, port=5000)
