import sqlite3
import os

class CocktailDatabase:
    def __init__(self, db_path='database/mixes.db'):
        self.db_path = db_path
        
        # Mapping: Zutat → pump_id (basierend auf ingredientID)
        self.ingredient_to_pump = {
            'Cola': 1, 'Limettensaft': 2, 'Zitronensaft': 3, 'Maracujasaft': 4,
            'Orangensaft': 5, 'Ananassaft': 6, 'Gernadine': 7, 'Kokossyrup': 8,
            'Tonic': 9, 'Havana': 10, 'Bacardi Hell': 11, 'Wodka': 12,
            'Gin': 13, 'Tequilla': 14, 'Pitu': 15, 'Whisky': 16,
            'Limette': 17, 'Rohrzucker': 18, 'Minze': 19
        }
        
        self._check_database_exists()

    def _check_database_exists(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Datenbank {self.db_path} nicht gefunden!")

    def get_available_cocktails(self, alkoholisch=None):
        """Verfügbare Cocktails mit Unterscheidung zwischen flüssig/manuell"""
        with sqlite3.connect(self.db_path) as conn:
            ingredient_columns = ', '.join([f'`{ingredient}`' for ingredient in self.ingredient_to_pump.keys()])
            
            if alkoholisch is None:
                query = f'SELECT ID, Getränk, {ingredient_columns}, Alkohol FROM mixes'
                cursor = conn.execute(query)
            else:
                query = f'SELECT ID, Getränk, {ingredient_columns}, Alkohol FROM mixes WHERE Alkohol = ?'
                cursor = conn.execute(query, (alkoholisch,))
            
            available_cocktails = []
            for row in cursor.fetchall():
                cocktail_id, name = row[0], row[1]
                alkohol_flag = row[-1]
                
                # Recipe aus Spalten-Werten erstellen
                liquid_recipe = []    # Zutaten zum Pumpen
                manual_ingredients = []  # Manuelle Zutaten
                
                for i, ingredient in enumerate(self.ingredient_to_pump.keys()):
                    amount_ml = row[2 + i]
                    if amount_ml and amount_ml > 0:
                        ingredient_id = self.ingredient_to_pump[ingredient]
                        is_liquid = self._is_liquid_ingredient(ingredient_id)
                        
                        if is_liquid:
                            # Flüssige Zutat → zum Pumpen
                            liquid_recipe.append({
                                'pump_id': ingredient_id - 1,  # pump_id startet bei 0
                                'ingredient_id': ingredient_id,
                                'ingredient_name': ingredient,
                                'amount_ml': amount_ml,
                                'is_liquid': True
                            })
                        else:
                            # Manuelle Zutat → Hinweis für Benutzer
                            manual_ingredients.append({
                                'ingredient_id': ingredient_id,
                                'ingredient_name': ingredient,
                                'amount_ml': amount_ml,
                                'is_liquid': False,
                                'instruction': self._get_manual_instruction(ingredient, amount_ml)
                            })
                
                # Nur verfügbare Cocktails (genug flüssige Zutaten)
                if self._can_make_cocktail(liquid_recipe):
                    available_cocktails.append({
                        'id': cocktail_id,
                        'name': name,
                        'image_path': "../images/" + name + ".png",
                        'liquid_recipe': liquid_recipe,  # Zum Pumpen
                        'manual_ingredients': manual_ingredients,  # Manuell hinzufügen
                        'alkoholisch': bool(alkohol_flag),
                        'glass_size_ml': 350,
                        'requires_manual_steps': len(manual_ingredients) > 0
                    })
            
            return available_cocktails

    def _is_liquid_ingredient(self, ingredient_id):
        """Prüft ob Zutat flüssig ist (isLiquid = 1)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT isLiquid FROM ingredients WHERE ingredientID = ?',
                (ingredient_id,)
            )
            result = cursor.fetchone()
            return result[0] == 1 if result else False

    def _get_manual_instruction(self, ingredient_name, amount):
        """Generiert Anweisungen für manuelle Zutaten"""
        instructions = {
            'Limette': f'Schneide {amount} Limettenscheibe(n) und gib sie ins Glas',
            'Rohrzucker': f'Füge {amount}g Rohrzucker hinzu',
            'Minze': f'Gib {amount} Minzblätter ins Glas und muddle sie leicht'
        }
        return instructions.get(ingredient_name, f'{ingredient_name} manuell hinzufügen: {amount} Einheit(en)')

    def _can_make_cocktail(self, liquid_recipe):
        """Prüfen ob genug flüssige Zutaten vorhanden"""
        with sqlite3.connect(self.db_path) as conn:
            for ingredient in liquid_recipe:
                cursor = conn.execute(
                    'SELECT currentLevel FROM ingredients WHERE ingredientID = ?',
                    (ingredient['ingredient_id'],)
                )
                result = cursor.fetchone()
                if not result or result[0] < ingredient['amount_ml']:
                    return False
        return True

    def get_ingredients_status(self):
        """Status aller Zutaten (ersetzt get_bottles_status)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT ingredientID, ingredient, isLiquid, currentLevel
                FROM ingredients ORDER BY ingredientID
            ''')
            
            ingredients = []
            for row in cursor.fetchall():
                ingredients.append({
                    'ingredient_id': row[0],
                    'ingredient_name': row[1],
                    'is_liquid': bool(row[2]),
                    'current_level': row[3],
                    'pump_id': row[0] - 1 if row[2] == 1 else None  # Nur für flüssige Zutaten
                })
            return ingredients

    def get_cocktail_by_id(self, cocktail_id):
        cocktails = self.get_available_cocktails()
        return next((c for c in cocktails if c['id'] == cocktail_id), None)

    def update_ingredient_level(self, ingredient_id, used_amount):
        """Reduziert den Level einer Zutat nach dem Mixen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE ingredients
                SET currentLevel = MAX(0, currentLevel - ?)
                WHERE ingredientID = ?
            ''', (used_amount, ingredient_id))
            
            cursor = conn.execute(
                'SELECT ingredient, currentLevel FROM ingredients WHERE ingredientID = ?',
                (ingredient_id,)
            )
            result = cursor.fetchone()
            if result:
                print(f"📉 {result[0]}: -{used_amount}ml (noch {result[1]}ml)")

    def set_ingredient_level(self, ingredient_id, new_level):
        """Setzt den Level einer Zutat auf einen bestimmten Wert"""
        new_level = max(0, new_level)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE ingredients 
                SET currentLevel = ? 
                WHERE ingredientID = ?
            ''', (new_level, ingredient_id))
            print(f"🔄 Zutat {ingredient_id} auf {new_level}ml gesetzt")

    def refill_ingredient(self, ingredient_id, add_amount):
        """Füllt eine Zutat additiv auf"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT currentLevel FROM ingredients WHERE ingredientID = ?',
                (ingredient_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return False
            
            current_level = result[0]
            new_level = max(0 ,current_level + add_amount)
            
            conn.execute('''
                UPDATE ingredients
                SET currentLevel = ?
                WHERE ingredientID = ?
            ''', (new_level, ingredient_id))
            
            print(f"🔄 Zutat {ingredient_id}: {current_level}ml + {add_amount}ml = {new_level}ml")
            return True

    def refill_all_ingredients(self, level):
        """Setzt alle Zutaten auf einen bestimmten Level"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE ingredients SET currentLevel = ?', (level,))
            updated_rows = cursor.rowcount
            conn.commit()
            print(f"🔄 Alle Zutaten auf {level}ml gesetzt ({updated_rows} Zutaten aktualisiert)")
            return updated_rows

    def get_alcoholic_cocktails(self):
        return self.get_available_cocktails(alkoholisch=1)

    def get_non_alcoholic_cocktails(self):
        return self.get_available_cocktails(alkoholisch=0)
