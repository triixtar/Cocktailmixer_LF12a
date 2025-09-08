import sqlite3
import os

class CocktailDatabase:
    def __init__(self, db_path='database/mixes.db'):
        self.db_path = db_path
        
        # Mapping: Zutat → pump_id (exakt wie in eurer CSV)
        self.ingredient_to_pump = {
            'Cola': 0, 'Limettensaft': 1, 'Zitronensaft': 2, 'Maracujasaft': 3,
            'Orangensaft': 4, 'Ananassaft': 5, 'Gernadine': 6, 'Kokossyrup': 7,
            'Tonic': 8, 'Havana': 9, 'Bacardi Hell': 10, 'Vodka': 11,  # ← Leerzeichen!
            'Gin': 12, 'Tequilla': 13, 'Pitu': 14, 'Whisky': 15,
            'Limette': 16, 'Rohrzucker': 17, 'Minze': 18
        }
        
        self._check_database_exists()

    def _check_database_exists(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Datenbank {self.db_path} nicht gefunden! Führe 'python scripts/init_db.py' aus.")

    def get_available_cocktails(self, alkoholisch=None):
        """Verfügbare Cocktails basierend auf eurer CSV-Struktur"""
        with sqlite3.connect(self.db_path) as conn:
            # Alle Zutaten-Spalten (mit Bacardi Hell statt Bacardi_Hell)
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
                alkohol_flag = row[-1]  # Letzter Wert
                
                # Recipe aus Spalten-Werten erstellen
                recipe = []
                for i, ingredient in enumerate(self.ingredient_to_pump.keys()):
                    amount_ml = row[2 + i]  # Ab Index 2 kommen die Zutaten
                    if amount_ml and amount_ml > 0:  # Nur verwendete Zutaten
                        recipe.append({
                            'pump_id': self.ingredient_to_pump[ingredient],
                            'ingredient_name': ingredient,
                            'amount_ml': amount_ml
                        })
                
                # Nur verfügbare Cocktails (genug Zutaten)
                if self._can_make_cocktail(recipe):
                    available_cocktails.append({
                        'id': cocktail_id,
                        'name': name,
                        'recipe': recipe,
                        'alkoholisch': bool(alkohol_flag),
                        'glass_size_ml': 350
                    })
            
            return available_cocktails

    def _can_make_cocktail(self, recipe):
        """Prüfen ob genug Zutaten vorhanden"""
        with sqlite3.connect(self.db_path) as conn:
            for ingredient in recipe:
                cursor = conn.execute(
                    'SELECT current_volume_ml FROM bottles WHERE pump_id = ?',
                    (ingredient['pump_id'],)
                )
                result = cursor.fetchone()
                if not result or result[0] < ingredient['amount_ml']:
                    return False
        return True

    def get_bottles_status(self):
        """Status aller Flaschen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT pump_id, ingredient_name, current_volume_ml
                FROM bottles ORDER BY pump_id
            ''')
            
            bottles = []
            for row in cursor.fetchall():
                bottles.append({
                    'pump_id': row[0],
                    'ingredient_name': row[1],
                    'current_volume_ml': row[2]
                })
            return bottles

    def get_cocktail_by_id(self, cocktail_id):
        cocktails = self.get_available_cocktails()
        return next((c for c in cocktails if c['id'] == cocktail_id), None)

    def update_bottle_volume(self, pump_id, used_ml):
        """Flascheninhalt nach dem Mixen reduzieren"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE bottles
                SET current_volume_ml = MAX(0, current_volume_ml - ?)
                WHERE pump_id = ?
            ''', (used_ml, pump_id))
            
            cursor = conn.execute(
                'SELECT ingredient_name, current_volume_ml FROM bottles WHERE pump_id = ?',
                (pump_id,)
            )
            result = cursor.fetchone()
            if result:
                print(f"📉 {result[0]}: -{used_ml}ml (noch {result[1]}ml)")

    def set_bottle_volume(self, pump_id, new_volume_ml):
        """Flascheninhalt auf bestimmte ML setzen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE bottles 
                SET current_volume_ml = ? 
                WHERE pump_id = ?
            ''', (new_volume_ml, pump_id))
            print(f"🔄 Pumpe {pump_id} auf {new_volume_ml}ml gesetzt")

    def refill_bottle(self, pump_id, add_volume):
        """Additiv auffüllen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT current_volume_ml FROM bottles WHERE pump_id = ?',
                (pump_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return False
            
            current_volume = result[0]
            new_volume = max(0, min(current_volume + add_volume, 1000))
            
            conn.execute('''
                UPDATE bottles
                SET current_volume_ml = ?
                WHERE pump_id = ?
            ''', (new_volume, pump_id))
            
            print(f"🔄 Pumpe {pump_id}: {current_volume}ml + {add_volume}ml = {new_volume}ml")
            return True

    def get_alcoholic_cocktails(self):
        return self.get_available_cocktails(alkoholisch=1)

    def get_non_alcoholic_cocktails(self):
        return self.get_available_cocktails(alkoholisch=0)
