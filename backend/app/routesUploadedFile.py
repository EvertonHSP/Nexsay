import os
from flask import Blueprint, send_from_directory, current_app


upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/uploads/fotos_perfil/<filename>')
def uploaded_file_perfil(filename):
    folder = os.path.join(current_app.root_path, "..",
                          "uploads", "fotos_perfil")
    folder = os.path.abspath(folder)
    return send_from_directory(folder, filename)
