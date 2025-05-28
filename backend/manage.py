from app import create_app
from app.extensions import db, socketio

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
    with app.app_context():
        db.create_all() 
        
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True,
        log_output=app.config['SOCKETIO_LOGGER']
    )