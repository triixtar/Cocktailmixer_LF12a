from flask import Blueprint, jsonify, request
from database.cocktail_db import CocktailDatabase
from core.pump_controller import PumpController
import threading

cocktails_bp = Blueprint('cocktails', __name__)

db = CocktailDatabase()
pump_controller = PumpController()

@cocktails_bp.route('/cocktails', methods=['GET'])
def get_cocktails():
    """Verfügbare Cocktails - optional gefiltert nach Alkohol"""
    alkohol_filter = request.args.get('alkoholisch')
    
    if alkohol_filter == 'true':
        cocktails = db.get_alcoholic_cocktails()
    elif alkohol_filter == 'false':
        cocktails = db.get_non_alcoholic_cocktails()
    else:
        cocktails = db.get_available_cocktails()
        
    return jsonify(cocktails)

@cocktails_bp.route('/cocktails/alcoholic', methods=['GET'])
def get_alcoholic_cocktails():
    """Nur alkoholische Cocktails"""
    cocktails = db.get_alcoholic_cocktails()
    return jsonify(cocktails)

@cocktails_bp.route('/cocktails/non-alcoholic', methods=['GET'])
def get_non_alcoholic_cocktails():
    """Nur alkoholfreie Cocktails"""
    cocktails = db.get_non_alcoholic_cocktails()
    return jsonify(cocktails)

@cocktails_bp.route('/bottles', methods=['GET'])
def get_bottles():
    """Status aller Flaschen"""
    bottles = db.get_bottles_status()
    return jsonify(bottles)

@cocktails_bp.route('/bottles/set', methods=['POST'])
def set_bottle_volume():
    """Flascheninhalt auf bestimmte ML setzen
    
    POST JSON: {"pump_id": 0, "volume": 500}
    """
    data = request.get_json()
    pump_id = data.get('pump_id')
    volume = data.get('volume')
    
    if pump_id is None or volume is None:
        return jsonify({'error': 'pump_id und volume sind erforderlich'}), 400
    
    if not isinstance(pump_id, int) or not isinstance(volume, (int, float)):
        return jsonify({'error': 'pump_id muss int und volume muss Zahl sein'}), 400
    
    if pump_id < 0 or pump_id > 18:  # ← Korrigiert: 19 Pumpen (0-18)
        return jsonify({'error': 'pump_id muss zwischen 0 und 18 liegen'}), 400
    
    if volume < 0:
        return jsonify({'error': 'volume darf nicht negativ sein'}), 400
    
    db.set_bottle_volume(pump_id, volume)
    return jsonify({
        'success': True,
        'pump_id': pump_id,
        'new_volume': volume,
        'message': f'Flasche {pump_id} auf {volume}ml gesetzt'
    })

@cocktails_bp.route('/bottles/refill', methods=['POST'])
def refill_bottle():
    """Flasche additiv auffüllen
    
    POST JSON: {"pump_id": 0, "volume": 200}
    -> Fügt 200ml zur aktuellen Menge hinzu
    """
    data = request.get_json()
    pump_id = data.get('pump_id')
    add_volume = data.get('volume')
    
    if pump_id is None or add_volume is None:
        return jsonify({'error': 'pump_id und volume sind erforderlich'}), 400
    
    if not isinstance(pump_id, int) or not isinstance(add_volume, (int, float)):
        return jsonify({'error': 'pump_id und volume müssen Zahlen sein'}), 400
    
    if pump_id < 0 or pump_id > 18:  # ← Korrigiert: 19 Pumpen (0-18)
        return jsonify({'error': 'pump_id muss zwischen 0 und 18 liegen'}), 400
    
    success = db.refill_bottle(pump_id, add_volume)
    if not success:
        return jsonify({'error': f'Pumpe {pump_id} nicht gefunden'}), 404
    
    # Neues Volumen für Response abrufen
    bottles = db.get_bottles_status()
    bottle = next((b for b in bottles if b['pump_id'] == pump_id), None)
    
    return jsonify({
        'success': True,
        'pump_id': pump_id,
        'added_volume': add_volume,
        'new_total': bottle['current_volume_ml'] if bottle else 0,
        'message': f'Flasche {pump_id}: +{add_volume}ml hinzugefügt'
    })

@cocktails_bp.route('/order', methods=['POST'])
def order_cocktail():
    """Cocktail bestellen und mixen"""
    data = request.get_json()
    cocktail_id = data.get('cocktail_id')
    
    cocktail = db.get_cocktail_by_id(cocktail_id)
    if not cocktail:
        return jsonify({'error': 'Cocktail nicht verfügbar'}), 400

    def mix_in_background():
        success = pump_controller.mix_cocktail(cocktail['recipe'], cocktail['name'])
        if success:
            for ingredient in cocktail['recipe']:
                db.update_bottle_volume(ingredient['pump_id'], ingredient['amount_ml'])

    threading.Thread(target=mix_in_background).start()
    
    return jsonify({
        'status': 'mixing',
        'cocktail': cocktail['name'],
        'alkoholisch': cocktail['alkoholisch'],
        'volume': f"{cocktail['glass_size_ml']}ml"
    })

@cocktails_bp.route('/status', methods=['GET'])
def get_status():
    """System-Status"""
    all_cocktails = db.get_available_cocktails()
    alcoholic = len(db.get_alcoholic_cocktails())
    non_alcoholic = len(db.get_non_alcoholic_cocktails())
    
    return jsonify({
        'is_mixing': pump_controller.is_mixing,
        'total_cocktails': len(all_cocktails),
        'alcoholic_cocktails': alcoholic,
        'non_alcoholic_cocktails': non_alcoholic
    })

@cocktails_bp.route('/test-pump/<int:pump_id>', methods=['POST'])  # ← Korrigiert
def test_pump(pump_id):
    """Einzelne Pumpe testen"""
    success = pump_controller.test_pump(pump_id)
    return jsonify({'success': success, 'pump_id': pump_id})
