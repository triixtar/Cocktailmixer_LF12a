from flask import Flask, jsonify
from flask_cors import CORS
from api.cocktails import cocktails_bp

app = Flask(__name__)
CORS(app)

# API-Routes registrieren
app.register_blueprint(cocktails_bp, url_prefix='/api')

@app.route('/')
def home():
    return jsonify({
        'message': 'Cocktail-Maschine Backend 🍸',
        'version': '1.0.0',
        'endpoints': {
            'cocktails': '/api/cocktails',
            'alcoholic': '/api/cocktails/alcoholic',
            'non_alcoholic': '/api/cocktails/non-alcoholic',
            'bottles': '/api/bottles',
            'order': '/api/order',
            'status': '/api/status',
            'test_pump': '/api/test-pump/<pump_id>'
        }
    })

if __name__ == '__main__':
    print("🚀 Starte Cocktail-Maschine Backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)
