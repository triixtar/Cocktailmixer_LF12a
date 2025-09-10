import time
import threading

class PumpController:
    def __init__(self):
        # GPIO-Pins für eure 19 Pumpen (0-18)
        self.pump_pins = [
            4, 17, 18, 27, 22, 23, 24, 25,    # Pumpen 0-7
            5, 6, 12, 13, 19, 16, 26, 20,     # Pumpen 8-15
            21, 7, 8                          # Pumpen 16-18 (Limette, Rohrzucker, Minze)
        ]
        
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            print("🔧 Hardware GPIO initialisiert")
        except ImportError:
            self.GPIO = self._create_dev_gpio()
            print("🔧 Development-Modus (Mock GPIO)")
            
        self.setup_gpio()
        self.is_mixing = False

    def _create_dev_gpio(self):
        """GPIO-Mock für Entwicklung"""
        class DevGPIO:
            BCM, OUT, HIGH, LOW = 'BCM', 'OUT', 1, 0
            def setmode(self, mode): pass
            def setup(self, pin, mode): pass
            def output(self, pin, state):
                action = "EIN" if state == self.LOW else "AUS"
                print(f"  GPIO {pin}: {action}")
            def cleanup(self): pass
        return DevGPIO()

    def setup_gpio(self):
        self.GPIO.setmode(self.GPIO.BCM)
        for pin in self.pump_pins:
            self.GPIO.setup(pin, self.GPIO.OUT)
            self.GPIO.output(pin, self.GPIO.HIGH)

    def run_pump(self, pump_id, amount_ml):
        """Einzelne Pumpe laufen lassen"""
        if pump_id < 0 or pump_id >= len(self.pump_pins):
            print(f"❌ Ungültige Pumpen-ID: {pump_id}")
            return False
            
        pin = self.pump_pins[pump_id]
        duration_sec = amount_ml * 0.5  # 2ml/s Kalibrierung
        
        print(f"🔄 Pumpe {pump_id} (GPIO {pin}): {amount_ml}ml für {duration_sec}s")
        
        self.GPIO.output(pin, self.GPIO.LOW)
        time.sleep(duration_sec)
        self.GPIO.output(pin, self.GPIO.HIGH)
        
        return True

    def mix_cocktail(self, recipe, cocktail_name="Cocktail"):
        """Kompletten Cocktail mixen"""
        self.is_mixing = True
        print(f"🍸 Mixe Cocktail: {cocktail_name}")
        
        threads = []
        for ingredient in recipe:
            pump_id = ingredient['pump_id']
            amount = ingredient['amount_ml']
            ingredient_name = ingredient['ingredient_name']
            
            print(f"  → {ingredient_name}: {amount}ml")
            t = threading.Thread(target=self.run_pump, args=(pump_id, amount))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()  # wait for every thread to finish

        print("✅ Cocktail fertig!")
        return True

    def test_pump(self, pump_id, duration_sec=2):
        """Einzelne Pumpe testen"""
        if pump_id < 0 or pump_id >= len(self.pump_pins):
            print(f"❌ Ungültige Pumpen-ID: {pump_id}")
            return False
            
        pin = self.pump_pins[pump_id]
        print(f"🔧 Test Pumpe {pump_id} (GPIO {pin}) für {duration_sec}s")
        
        self.GPIO.output(pin, self.GPIO.LOW)
        time.sleep(duration_sec)
        self.GPIO.output(pin, self.GPIO.HIGH)
        return True

    def cleanup(self):
        self.GPIO.cleanup()
        print("🧹 GPIO cleanup abgeschlossen")
