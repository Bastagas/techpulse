"""Flask application factory.

Sprint 0 : stub minimal. L'implémentation réelle arrive en Sprint 3.
"""

from __future__ import annotations


def create_app():
    """Factory Flask. Stub du Sprint 0."""
    from flask import Flask

    app = Flask(__name__)

    @app.route("/health")
    def health():
        return {"status": "ok", "sprint": 0, "message": "API stub — impl en Sprint 3"}

    return app


def run() -> None:
    """Entry point : `python -m techpulse_api`."""
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    run()
