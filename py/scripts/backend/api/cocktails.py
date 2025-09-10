from flask import Blueprint, jsonify, request
from database.cocktail_db import CocktailDatabase
from core.pump_controller import PumpController
import threading

cocktails_bp = Blueprint('cocktails', __name__)

db = CocktailDatabase()
pump_controller = PumpController()

@cocktails_bp.route('/cocktails', methods=['GET'])
def get_cocktails():
    """Verfügbare Cocktails - mit manuellen Schritten"""
    alkohol_filter = request.args.get('alkoholisch')
    
    if alkohol_filter == 'true':
        cocktails = db.get_alcoholic_cocktails()
    elif alkohol_filter == 'false':
        cocktails = db.get_non_alcoholic_cocktails()
    else:
        cocktails = db.get_available_cocktails()
        
    return jsonify(cocktails)

@cocktails_bp.route('/ingredients', methods=['GET'])  # Neuer Endpoint
def get_ingredients():
    """Status aller Zutaten (ersetzt /bottles)"""
    ingredients = db.get_ingredients_status()
    return jsonify(ingredients)

@cocktails_bp.route('/ingredients/set', methods=['POST'])
def set_ingredient_level():
    """Zutat auf bestimmten Level setzen
    
    POST JSON: {"ingredient_id": 1, "level": 500}
    """
    data = request.get_json()
    ingredient_id = data.get('ingredient_id')
    level = data.get('level')
    
    if ingredient_id is None or level is None:
        return jsonify({'error': 'ingredient_id und level sind erforderlich'}), 400
    
    if not isinstance(ingredient_id, int) or not isinstance(level, (int, float)):
        return jsonify({'error': 'ingredient_id und level müssen Zahlen sein'}), 400
    
    if ingredient_id < 1 or ingredient_id > 19:
        return jsonify({'error': 'ingredient_id muss zwischen 1 und 19 liegen'}), 400
    
    if level < 0:
        return jsonify({'error': 'level darf nicht negativ sein'}), 400
    
    db.set_ingredient_level(ingredient_id, level)
    return jsonify({
        'success': True,
        'ingredient_id': ingredient_id,
        'new_level': level,
        'message': f'Zutat {ingredient_id} auf {level}ml gesetzt'
    })

@cocktails_bp.route('/ingredients/refill', methods=['POST'])
def refill_ingredient():
    """Zutat additiv auffüllen
    
    POST JSON: {"ingredient_id": 1, "amount": 200}
    """
    data = request.get_json()
    ingredient_id = data.get('ingredient_id')
    add_amount = data.get('amount')
    
    if ingredient_id is None or add_amount is None:
        return jsonify({'error': 'ingredient_id und amount sind erforderlich'}), 400
    
    if not isinstance(ingredient_id, int) or not isinstance(add_amount, (int, float)):
        return jsonify({'error': 'ingredient_id und amount müssen Zahlen sein'}), 400
    
    if ingredient_id < 1 or ingredient_id > 19:
        return jsonify({'error': 'ingredient_id muss zwischen 1 und 19 liegen'}), 400
    
    success = db.refill_ingredient(ingredient_id, add_amount)
    if not success:
        return jsonify({'error': f'Zutat {ingredient_id} nicht gefunden'}), 404
    
    # Neuen Level für Response abrufen
    ingredients = db.get_ingredients_status()
    ingredient = next((i for i in ingredients if i['ingredient_id'] == ingredient_id), None)
    
    return jsonify({
        'success': True,
        'ingredient_id': ingredient_id,
        'added_amount': add_amount,
        'new_level': ingredient['current_level'] if ingredient else 0,
        'message': f'Zutat {ingredient_id}: +{add_amount}ml hinzugefügt'
    })

@cocktails_bp.route('/ingredients/refill_all', methods=['POST'])
def refill_all_ingredients():
    """Alle Zutaten auf bestimmten Level setzen
    
    POST JSON: {"level": 2000} (optional, Standard: 2000)
    """
    data = request.get_json() or {}
    level = data.get('level', 2000)  # Standard: 2000ml
    
    if not isinstance(level, (int, float)) or level < 0:
        return jsonify({'error': 'level muss eine positive Zahl sein'}), 400
    
    updated_count = db.refill_all_ingredients(level)
    
    if updated_count > 0:
        # Neuen Status aller Zutaten abrufen
        ingredients = db.get_ingredients_status()
        
        return jsonify({
            'success': True,
            'level_set': level,
            'updated_count': updated_count,
            'ingredients_status': ingredients,
            'message': f'Alle {updated_count} Zutaten auf {level}ml gesetzt'
        })
    else:
        return jsonify({'error': 'Keine Zutaten gefunden oder Update fehlgeschlagen'}), 404

@cocktails_bp.route('/order', methods=['POST'])
def order_cocktail():
    """Cocktail bestellen und mixen - mit manuellen Schritten"""
    data = request.get_json()
    cocktail_id = data.get('cocktail_id')
    
    cocktail = db.get_cocktail_by_id(cocktail_id)
    if not cocktail:
        return jsonify({'error': 'Cocktail nicht verfügbar'}), 400

    def mix_in_background():
        # Nur die flüssigen Zutaten pumpen
        success = pump_controller.mix_cocktail(cocktail['liquid_recipe'], cocktail['name'])
        if success:
            # Level der flüssigen Zutaten reduzieren
            for ingredient in cocktail['liquid_recipe']:
                db.update_ingredient_level(ingredient['ingredient_id'], ingredient['amount_ml'])

    threading.Thread(target=mix_in_background).start()
    
    response = {
        'status': 'mixing',
        'cocktail': cocktail['name'],
        'alkoholisch': cocktail['alkoholisch'],
        'volume': f"{cocktail['glass_size_ml']}ml",
        'liquid_ingredients': cocktail['liquid_recipe'],  # Was gepumpt wird
        'manual_steps': cocktail['manual_ingredients'] if cocktail['requires_manual_steps'] else []
    }
    
    if cocktail['requires_manual_steps']:
        response['message'] = 'Cocktail wird gemischt. Bitte folgende Zutaten manuell hinzufügen:'
        response['instructions'] = [step['instruction'] for step in cocktail['manual_ingredients']]
    
    return jsonify(response)

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

@cocktails_bp.route('/test-pump/<int:pump_id>', methods=['POST'])
def test_pump(pump_id):
    """Einzelne Pumpe testen"""
    success = pump_controller.test_pump(pump_id)
    return jsonify({'success': success, 'pump_id': pump_id})
