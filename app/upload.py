"""
File upload and Excel preview routes.
"""

import os
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from .models import Upload, db

bp = Blueprint("upload", __name__)


def _normalize_json_value(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-safe Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _allowed_file(filename: str, file_type: str) -> bool:
    if file_type not in current_app.config["ALLOWED_EXTENSIONS"]:
        return False
    _, ext = os.path.splitext(filename)
    return ext.lower() in current_app.config["ALLOWED_EXTENSIONS"][file_type]


def _detect_file_type(filename: str) -> str | None:
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    for file_type, extensions in current_app.config["ALLOWED_EXTENSIONS"].items():
        if ext in extensions:
            return file_type
    return None


def _safe_preview_stats(df_raw: pd.DataFrame, df_cleaned: pd.DataFrame) -> Dict[str, Any]:
    dtype_counts = df_cleaned.dtypes.value_counts().to_dict()
    missing_by_col = df_cleaned.isnull().sum().to_dict()
    numeric_stats: Dict[str, Dict[str, Any]] = {}

    numeric_df = df_cleaned.select_dtypes(include=["number"])
    if not numeric_df.empty:
        described = numeric_df.describe().to_dict()
        for col, values in described.items():
            numeric_stats[col] = {k: _normalize_json_value(v) for k, v in values.items()}

    return {
        "row_count": int(len(df_cleaned)),
        "column_count": int(len(df_cleaned.columns)),
        "data_types": {str(k): int(v) for k, v in dtype_counts.items()},
        "missing_values_total": int(df_cleaned.isnull().sum().sum()),
        "missing_values_by_column": {str(k): int(v) for k, v in missing_by_col.items()},
        "numeric_stats": numeric_stats,
        "preprocessing": {
            "original_shape": [int(df_raw.shape[0]), int(df_raw.shape[1])],
            "cleaned_shape": [int(df_cleaned.shape[0]), int(df_cleaned.shape[1])],
            "removed_empty_rows": int(df_raw.shape[0] - df_raw.dropna(how="all").shape[0]),
            "removed_empty_columns": int(df_raw.shape[1] - df_raw.dropna(axis=1, how="all").shape[1]),
        },
    }


@bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """Upload a file and persist file metadata."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file selected"}), 400

    file = request.files["file"]
    file_type = request.form.get("file_type", "").strip()

    if not file.filename:
        return jsonify({"success": False, "message": "No file selected"}), 400

    if not file_type:
        file_type = _detect_file_type(file.filename) or ""

    if not file_type:
        return jsonify({"success": False, "message": "Unsupported file type"}), 400

    if not _allowed_file(file.filename, file_type):
        allowed = current_app.config["ALLOWED_EXTENSIONS"].get(file_type, [])
        return jsonify(
            {
                "success": False,
                "message": f"File extension not allowed. Allowed for {file_type}: {allowed}",
            }
        ), 400

    original_filename = file.filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = secure_filename(f"{timestamp}_{original_filename}")

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, safe_filename)
    file.save(file_path)

    upload = Upload(
        filename=safe_filename,
        original_filename=original_filename,
        file_size=os.path.getsize(file_path),
        file_type=file_type,
        upload_path=file_path,
        user_id=current_user.id,
    )
    db.session.add(upload)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Upload successful",
            "data": {
                "id": upload.id,
                "filename": upload.filename,
                "original_filename": upload.original_filename,
                "file_size": upload.file_size,
                "file_type": upload.file_type,
                "uploaded_at": upload.uploaded_at.isoformat(),
            },
        }
    )


@bp.route("/uploads", methods=["GET"])
@login_required
def get_uploads():
    """Return upload history for current user."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    uploads = (
        Upload.query.filter_by(user_id=current_user.id)
        .order_by(Upload.uploaded_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": upload.id,
                        "filename": upload.filename,
                        "original_filename": upload.original_filename,
                        "file_size": upload.file_size,
                        "file_type": upload.file_type,
                        "uploaded_at": upload.uploaded_at.isoformat(),
                    }
                    for upload in uploads.items
                ],
                "total": uploads.total,
                "page": uploads.page,
                "pages": uploads.pages,
                "per_page": uploads.per_page,
            },
        }
    )


@bp.route("/excel/preview/<int:file_id>", methods=["GET"])
@login_required
def preview_excel(file_id: int):
    """
    Preview tabular files.
    Supports .csv, .xlsx, .xls and returns both modern and compatibility fields.
    """
    upload = Upload.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not upload:
        return jsonify({"success": False, "message": "File not found or access denied"}), 404

    if not os.path.exists(upload.upload_path):
        return jsonify({"success": False, "message": "File does not exist on server"}), 404

    if os.path.getsize(upload.upload_path) == 0:
        return jsonify({"success": False, "message": "Empty file"}), 400

    _, ext = os.path.splitext(upload.filename or upload.original_filename)
    ext = ext.lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        return jsonify({"success": False, "message": "Unsupported file format"}), 400

    try:
        if ext == ".csv":
            df_raw = pd.read_csv(upload.upload_path)
        else:
            df_raw = pd.read_excel(upload.upload_path, engine="openpyxl")

        df_cleaned = df_raw.dropna(how="all").dropna(axis=1, how="all")
        stats = _safe_preview_stats(df_raw, df_cleaned)

        preview_df = df_cleaned.head(10)
        preview_data = []
        for row in preview_df.to_dict(orient="records"):
            preview_data.append({str(k): _normalize_json_value(v) for k, v in row.items()})

        columns_info = []
        for col in df_cleaned.columns:
            series = df_cleaned[col]
            sample_value = _normalize_json_value(series.iloc[0]) if len(series) > 0 else None
            columns_info.append(
                {
                    "name": str(col),
                    "type": str(series.dtype),
                    "non_null_count": int(series.count()),
                    "unique_count": int(series.nunique(dropna=True)),
                    "sample_value": sample_value,
                }
            )

        response_data = {
            "success": True,
            # compatibility shape used by tests
            "data": preview_data,
            "stats": stats,
            # legacy fields
            "preview": preview_data,
            "statistics": {
                "total_rows": stats["row_count"],
                "total_cols": stats["column_count"],
                "dtype_distribution": stats["data_types"],
            },
            "columns_info": columns_info,
            "filename": upload.original_filename,
            "file_type": upload.file_type,
            "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
        }
        return jsonify(response_data)

    except pd.errors.EmptyDataError:
        return jsonify({"success": False, "message": "File content is empty"}), 400
    except pd.errors.ParserError as exc:
        return jsonify({"success": False, "message": f"Failed to parse file: {exc}"}), 400
    except Exception as exc:
        current_app.logger.exception("Failed to preview file")
        return jsonify({"success": False, "message": f"Failed to read file: {exc}"}), 500
