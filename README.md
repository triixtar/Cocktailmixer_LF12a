# Coctailmixer_LF12a

# backend python requiremnts installieren: pip install -r requirements.txt

# backend starten mit python app.py

# Endpunkte übersichts Seite http://localhost:5000/

endpoints:
| `/api/cocktails` | GET | Alle verfügbaren Cocktails |
| `/api/cocktails/alcoholic` | GET | Nur alkoholische Cocktails |
| `/api/cocktails/non-alcoholic` | GET | Nur alkoholfreie Cocktails |
| `/api/ingredients` | GET | Status aller Zutaten/Flaschen |
| `/api/ingredients/set` | POST | Zutat auf bestimmten Level setzen |
| `/api/ingredients/refill` | POST | Zutat auffüllen |
| `/api/ingredients/refill_all` | POST | Alle Zutaten auf Level setzen |
| `/api/order` | POST | Cocktail bestellen und mixen |
| `/api/status` | GET | System-Status |
| `/api/test-pump/<pump_id>` | POST | Einzelne Pumpe testen |

Beispiel call: http://localhost:5000/api/order
Message:
{
"cocktail_id": 1
}

Response: {
"status": "mixing",
"cocktail": "Gin Tonic",
"alkoholisch": true,
"volume": "350ml",
"liquid_ingredients": [
{"pump_id": 8, "ingredient_name": "Tonic", "amount_ml": 260},
{"pump_id": 12, "ingredient_name": "Gin", "amount_ml": 90}
],
"manual_steps": [
{"ingredient_name": "Limette", "instruction": "Schneide 1 Limettenscheibe und gib sie ins Glas"}
]
}
