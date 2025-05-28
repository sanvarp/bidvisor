import os
import traceback

from models import db
from config import Config
from flask import Flask, jsonify, send_from_directory

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)

    # Crear la carpeta de subidas si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Registrar Blueprints
    from routes.session_routes import session_bp
    from routes.upload_routes import upload_bp
    from routes.ask_routes import ask_bp
    from routes.process_routes import process_bp
    from routes.home_routes import home_bp

    app.register_blueprint(session_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(ask_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(home_bp)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.errorhandler(Exception)
    def handle_exception(e):
        """ Captura cualquier error en la aplicación y lo imprime en la consola """
        print("ERROR DETECTADO:")
        print(traceback.format_exc())  # Muestra el error detallado en la consola
        return jsonify({"error": str(e)}), 500

    return app

# Crear la aplicación a nivel global para que Gunicorn la detecte
app = create_app()

# Crear las tablas en la base de datos si no existen
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)