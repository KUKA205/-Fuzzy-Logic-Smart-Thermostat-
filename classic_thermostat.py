"""
Классический термостат на if-else.
Используется для сравнения с нечёткой логикой.
"""

import numpy as np


class ClassicThermostat:
    """
    Простой термостат с пороговой логикой.
    
    Зоны температуры:
      < 18°C  → максимальный обогрев
      18-20°C → умеренный обогрев
      20-24°C → выключено
      24-27°C → умеренное охлаждение
      > 27°C  → максимальное охлаждение
    
    Влажность корректирует мощность на ±10%.
    Время суток снижает мощность ночью на 20%.
    """

    # Пороги температуры
    TEMP_COLD_MAX   = 18.0
    TEMP_COOL_MAX   = 20.0
    TEMP_COMFORT_LO = 20.0
    TEMP_COMFORT_HI = 24.0
    TEMP_WARM_MAX   = 27.0

    # Уровни мощности
    POWER_STRONG = 100.0
    POWER_MILD   =  50.0
    POWER_OFF    =   0.0

    def __init__(self, target_temp: float = 22.0):
        self.target_temp = target_temp
        self._mode = 'off'       # текущий режим для гистерезиса
        self._last_power = 0.0

    def compute(self, temperature: float,
                humidity: float,
                time_of_day: float) -> float:
        """
        Вычислить мощность (пороговая логика).

        Returns
        -------
        float — (-100 обогрев … +100 охлаждение)
        """
        temperature = float(temperature)
        humidity    = float(humidity)
        time_of_day = float(time_of_day)

        # ── Базовая мощность по температуре ──────────────────────────
        if temperature < self.TEMP_COLD_MAX:
            power = -self.POWER_STRONG   # сильный обогрев

        elif temperature < self.TEMP_COOL_MAX:
            power = -self.POWER_MILD     # умеренный обогрев

        elif temperature <= self.TEMP_COMFORT_HI:
            power = self.POWER_OFF       # комфортная зона

        elif temperature <= self.TEMP_WARM_MAX:
            power = self.POWER_MILD      # умеренное охлаждение

        else:
            power = self.POWER_STRONG    # сильное охлаждение

        # ── Коррекция на влажность ────────────────────────────────────
        if humidity > 70:
            # Высокая влажность → усиливаем охлаждение / снижаем обогрев
            if power > 0:
                power = min(power * 1.15, 100.0)
            elif power < 0:
                power = max(power * 0.85, -100.0)
        elif humidity < 30:
            # Низкая влажность → снижаем охлаждение
            if power > 0:
                power *= 0.9

        # ── Коррекция на время суток (ночной режим) ───────────────────
        is_night = (time_of_day >= 22) or (time_of_day < 6)
        if is_night:
            power *= 0.75   # тише ночью

        self._last_power = power
        return power

    def get_mode(self, power: float) -> str:
        """Текстовое описание режима."""
        if power < -50:
            return "🔥 Сильный обогрев"
        elif power < 0:
            return "🌡️ Умеренный обогрев"
        elif power == 0:
            return "✅ Выключено"
        elif power < 50:
            return "❄️ Умеренное охлаждение"
        else:
            return "🧊 Сильное охлаждение"

    def describe_rules(self) -> str:
        """Описание правил if-else."""
        return """
╔══════════════════════════════════════════════════╗
║         ПРАВИЛА КЛАССИЧЕСКОГО ТЕРМОСТАТА          ║
╠══════════════════════════════════════════════════╣
║ T < 18°C          → Мощность: -100% (обогрев)   ║
║ 18°C ≤ T < 20°C   → Мощность: -50%  (обогрев)   ║
║ 20°C ≤ T ≤ 24°C   → Мощность: 0%   (выкл.)      ║
║ 24°C < T ≤ 27°C   → Мощность: +50% (охлажд.)    ║
║ T > 27°C           → Мощность: +100%(охлажд.)    ║
╠══════════════════════════════════════════════════╣
║ + Влажность >70%:  усилить охлаждение на 15%     ║
║ + Влажность <30%:  снизить охлаждение на 10%     ║
║ + Ночь (22-06):    снизить мощность на 25%        ║
╚══════════════════════════════════════════════════╝
"""
