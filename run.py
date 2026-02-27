#!/usr/bin/env python3
"""
Office Assistant startup script.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


app = create_app()


if __name__ == "__main__":
    env_name = app.config.get("ENV") or os.environ.get("FLASK_ENV") or "production"
    print("=" * 60)
    print("Office Assistant v1.0.0")
    print("=" * 60)
    print(f"Environment: {env_name}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"Upload folder: {app.config.get('UPLOAD_FOLDER')}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
