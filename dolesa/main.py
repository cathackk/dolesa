import os

from flask import Flask

from dolesa.dolesa import bp as dolesa_bp

app = Flask(__name__)
app.register_blueprint(dolesa_bp, url_prefix='/dolesa')


if __name__ == '__main__':
    app.run(
        debug=False,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
    )
