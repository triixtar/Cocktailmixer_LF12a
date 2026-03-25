from flask import Blueprint, jsonify, request
from database.cocktail_db import CocktailDatabase
from core.pump_controller import PumpController
import threading

cocktails_bp = Blueprint('cocktails', __name__)

db = CocktailDatabase()
pump_controller = PumpController()

# ─────────────────────────────────────────────────────────────────────────────
# Cocktails
# ─────────────────────────────────────────────────────────────────────────────

@cocktails_bp.route('/cocktails', methods=['GET'])
def get_cocktails():
    alkohol_filter = request.args.get('alkoholisch')
    if alkohol_filter == 'true':
        cocktails = db.get_alcoholic_cocktails()
    elif alkohol_filter == 'false':
        cocktails = db.get_non_alcoholic_cocktails()
    else:
        cocktails = db.get_available_cocktails()
    return jsonify(cocktails)


@cocktails_bp.route('/order', methods=['POST'])
def order_cocktail():
    data = request.get_json()
    cocktail_id = data.get('cocktail_id')

    cocktail = db.get_cocktail_by_id(cocktail_id)
    if not cocktail:
        return jsonify({'error': 'Cocktail nicht verfügbar'}), 400

    def mix_in_background():
        success = pump_controller.mix_cocktail(cocktail['liquid_recipe'], cocktail['name'])
        if success:
            for ingredient in cocktail['liquid_recipe']:
                db.update_ingredient_level(ingredient['ingredient_id'], ingredient['amount_ml'])

    threading.Thread(target=mix_in_background).start()

    response = {
        'status': 'mixing',
        'cocktail': cocktail['name'],
        'alkoholisch': cocktail['alkoholisch'],
        'volume': f"{cocktail['glass_size_ml']}ml",
        'liquid_ingredients': cocktail['liquid_recipe'],
        'manual_steps': cocktail['manual_ingredients'] if cocktail['requires_manual_steps'] else [],
    }
    if cocktail['requires_manual_steps']:
        response['message'] = 'Cocktail wird gemischt. Bitte folgende Zutaten manuell hinzufügen:'
        response['instructions'] = [s['instruction'] for s in cocktail['manual_ingredients']]

    return jsonify(response)


@cocktails_bp.route('/status', methods=['GET'])
def get_status():
    all_cocktails = db.get_available_cocktails()
    return jsonify({
        'is_mixing': pump_controller.is_mixing,
        'total_cocktails': len(all_cocktails),
        'alcoholic_cocktails': len(db.get_alcoholic_cocktails()),
        'non_alcoholic_cocktails': len(db.get_non_alcoholic_cocktails()),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Ingredients
# ─────────────────────────────────────────────────────────────────────────────

@cocktails_bp.route('/ingredients', methods=['GET'])
def get_ingredients():
    return jsonify(db.get_ingredients_status())


@cocktails_bp.route('/ingredients/set', methods=['POST'])
def set_ingredient_level():
    """POST JSON: {"ingredient_id": 1, "level": 500}"""
    data = request.get_json()
    ingredient_id = data.get('ingredient_id')
    level = data.get('level')

    if ingredient_id is None or level is None:
        return jsonify({'error': 'ingredient_id und level sind erforderlich'}), 400
    if not isinstance(ingredient_id, int) or not isinstance(level, (int, float)):
        return jsonify({'error': 'ingredient_id und level müssen Zahlen sein'}), 400
    if level < 0:
        return jsonify({'error': 'level darf nicht negativ sein'}), 400

    db.set_ingredient_level(ingredient_id, level)
    return jsonify({
        'success': True,
        'ingredient_id': ingredient_id,
        'new_level': level,
        'max_level': level,
        'message': f'Zutat {ingredient_id} auf {level}ml gesetzt',
    })


@cocktails_bp.route('/ingredients/refill', methods=['POST'])
def refill_ingredient():
    """POST JSON: {"ingredient_id": 1, "amount": 200}"""
    data = request.get_json()
    ingredient_id = data.get('ingredient_id')
    add_amount = data.get('amount')

    if ingredient_id is None or add_amount is None:
        return jsonify({'error': 'ingredient_id und amount sind erforderlich'}), 400
    if not isinstance(ingredient_id, int) or not isinstance(add_amount, (int, float)):
        return jsonify({'error': 'ingredient_id und amount müssen Zahlen sein'}), 400

    success = db.refill_ingredient(ingredient_id, add_amount)
    if not success:
        return jsonify({'error': f'Zutat {ingredient_id} nicht gefunden'}), 404

    ingredients = db.get_ingredients_status()
    ingredient = next((i for i in ingredients if i['ingredient_id'] == ingredient_id), None)

    return jsonify({
        'success': True,
        'ingredient_id': ingredient_id,
        'added_amount': add_amount,
        'new_level': ingredient['current_level'] if ingredient else 0,
        'max_level': ingredient['max_level'] if ingredient else 0,
        'message': f'Zutat {ingredient_id}: +{add_amount}ml hinzugefügt',
    })


@cocktails_bp.route('/ingredients/refill_all', methods=['POST'])
def refill_all_ingredients():
    """POST JSON: {"level": 2000}  (default: 2000)"""
    data = request.get_json() or {}
    level = data.get('level', 2000)

    if not isinstance(level, (int, float)) or level < 0:
        return jsonify({'error': 'level muss eine positive Zahl sein'}), 400

    updated_count = db.refill_all_ingredients(level)
    if not updated_count:
        return jsonify({'error': 'Keine Zutaten gefunden oder Update fehlgeschlagen'}), 404

    return jsonify({
        'success': True,
        'level_set': level,
        'updated_count': updated_count,
        'ingredients_status': db.get_ingredients_status(),
        'message': f'Alle {updated_count} Zutaten auf {level}ml gesetzt',
    })


# ─────────────────────────────────────────────────────────────────────────────
# Pumps
# ─────────────────────────────────────────────────────────────────────────────

@cocktails_bp.route('/test-pump/<int:pump_id>', methods=['POST'])
def test_pump(pump_id):
    success = pump_controller.test_pump(pump_id)
    return jsonify({'success': success, 'pump_id': pump_id})


# ─────────────────────────────────────────────────────────────────────────────
# PIN management
# ─────────────────────────────────────────────────────────────────────────────

import json, os

ALCOHOL_PIN_FILE = "data/pin.json"
ADMIN_PIN = "9999"


def load_alcohol_pin():
    if os.path.exists(ALCOHOL_PIN_FILE):
        try:
            with open(ALCOHOL_PIN_FILE) as f:
                p = str(json.load(f).get("alcohol_pin", "1234"))
                if p.isdigit() and len(p) == 4:
                    return p
        except Exception:
            pass
    return "1234"


def save_alcohol_pin(pin):
    os.makedirs(os.path.dirname(ALCOHOL_PIN_FILE), exist_ok=True)
    with open(ALCOHOL_PIN_FILE, "w") as f:
        json.dump({"alcohol_pin": pin}, f)


CURRENT_ALCOHOL_PIN = load_alcohol_pin()


@cocktails_bp.route('/check-pin', methods=['POST'])
def check_pin():
    """POST JSON: {"pin": "1234", "purpose": "alcohol"|"admin"}"""
    data = request.get_json()
    if not data or 'pin' not in data:
        return jsonify({'error': 'PIN erforderlich'}), 400

    pin = str(data.get('pin'))
    purpose = str(data.get('purpose', 'alcohol'))

    if not pin.isdigit() or len(pin) != 4:
        return jsonify({'error': 'PIN muss 4 Ziffern sein'}), 400

    is_valid = (pin == ADMIN_PIN) if purpose == 'admin' else (pin == CURRENT_ALCOHOL_PIN)
    return jsonify({'valid': is_valid, 'message': 'PIN korrekt' if is_valid else 'PIN falsch'})


@cocktails_bp.route('/change-pin', methods=['POST'])
def change_pin():
    """POST JSON: {"old_pin": "1234", "new_pin": "5678"}"""
    global CURRENT_ALCOHOL_PIN

    data = request.get_json()
    if not data or 'old_pin' not in data or 'new_pin' not in data:
        return jsonify({'error': 'old_pin und new_pin erforderlich'}), 400

    old_pin, new_pin = str(data['old_pin']), str(data['new_pin'])

    if not old_pin.isdigit() or len(old_pin) != 4:
        return jsonify({'error': 'Alte PIN muss 4 Ziffern sein'}), 400
    if not new_pin.isdigit() or len(new_pin) != 4:
        return jsonify({'error': 'Neue PIN muss 4 Ziffern sein'}), 400
    if old_pin != CURRENT_ALCOHOL_PIN:
        return jsonify({'success': False, 'message': 'Alte PIN falsch'}), 401

    CURRENT_ALCOHOL_PIN = new_pin
    save_alcohol_pin(new_pin)
    return jsonify({'success': True, 'message': 'PIN erfolgreich geändert'})