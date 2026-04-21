"""
Умный термостат на нечёткой логике
Входы: температура, влажность, время суток
Выход: мощность системы отопления/охлаждения
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class FuzzyThermostat:
    """
    Нечёткий термостат с 3 входами и 1 выходом.
    
    Логика:
      + мощность → охлаждение  
      - мощность → обогрев
    """

    def __init__(self, target_temp: float = 22.0):
        self.target_temp = target_temp
        self._build_universe()
        self._build_membership_functions()
        self._build_rules()
        self._build_system()

    # ------------------------------------------------------------------ #
    #  1. UNIVERSES — диапазоны входных/выходных переменных               #
    # ------------------------------------------------------------------ #
    def _build_universe(self):
        # Температура: 0..40 °C
        self.temperature = ctrl.Antecedent(np.arange(0, 41, 1), 'temperature')
        # Влажность: 0..100 %
        self.humidity = ctrl.Antecedent(np.arange(0, 101, 1), 'humidity')
        # Время суток: 0..24 ч
        self.time_of_day = ctrl.Antecedent(np.arange(0, 25, 1), 'time_of_day')
        # Мощность: -100..+100 %  (- обогрев, + охлаждение)
        self.power = ctrl.Consequent(np.arange(-100, 101, 1), 'power')

    # ------------------------------------------------------------------ #
    #  2. MEMBERSHIP FUNCTIONS — функции принадлежности                   #
    # ------------------------------------------------------------------ #
    def _build_membership_functions(self):

        # ── Температура ────────────────────────────────────────────────
        self.temperature['cold']   = fuzz.trimf(self.temperature.universe,
                                                  [0,  0, 18])
        self.temperature['normal'] = fuzz.trimf(self.temperature.universe,
                                                  [16, 22, 28])
        self.temperature['hot']    = fuzz.trimf(self.temperature.universe,
                                                  [25, 40, 40])

        # ── Влажность ──────────────────────────────────────────────────
        self.humidity['low']    = fuzz.trimf(self.humidity.universe,
                                              [0,   0,  40])
        self.humidity['medium'] = fuzz.trimf(self.humidity.universe,
                                              [30,  55,  70])
        self.humidity['high']   = fuzz.trimf(self.humidity.universe,
                                              [60, 100, 100])

        # ── Время суток ────────────────────────────────────────────────
        # ночь 22:00-06:00, день 10:00-18:00, переход 06-10 / 18-22
        self.time_of_day['night']      = fuzz.trapmf(self.time_of_day.universe,
                                                      [0, 0, 5, 7])
        self.time_of_day['morning']    = fuzz.trimf(self.time_of_day.universe,
                                                     [6, 9, 12])
        self.time_of_day['afternoon']  = fuzz.trimf(self.time_of_day.universe,
                                                     [11, 15, 19])
        self.time_of_day['evening']    = fuzz.trimf(self.time_of_day.universe,
                                                     [17, 20, 23])
        self.time_of_day['late_night'] = fuzz.trapmf(self.time_of_day.universe,
                                                      [21, 23, 24, 24])

        # ── Мощность ───────────────────────────────────────────────────
        self.power['strong_heat']  = fuzz.trimf(self.power.universe,
                                                 [-100, -100, -50])
        self.power['mild_heat']    = fuzz.trimf(self.power.universe,
                                                 [-70,  -35,   0])
        self.power['off']          = fuzz.trimf(self.power.universe,
                                                 [-20,    0,  20])
        self.power['mild_cool']    = fuzz.trimf(self.power.universe,
                                                 [  0,   35,  70])
        self.power['strong_cool']  = fuzz.trimf(self.power.universe,
                                                 [ 50,  100, 100])

    # ------------------------------------------------------------------ #
    #  3. RULES — 9 правил нечёткой логики                               #
    # ------------------------------------------------------------------ #
    def _build_rules(self):
        T = self.temperature
        H = self.humidity
        TOD = self.time_of_day
        P = self.power

        self.rules = [
            # Правило 1: Холодно → сильный обогрев
            ctrl.Rule(T['cold'] & H['low'],
                      P['strong_heat']),

            # Правило 2: Холодно + влажно → умеренный обогрев
            ctrl.Rule(T['cold'] & H['high'],
                      P['mild_heat']),

            # Правило 3: Нормальная температура → выключено
            ctrl.Rule(T['normal'],
                      P['off']),

            # Правило 4: Жарко → сильное охлаждение
            ctrl.Rule(T['hot'] & H['high'],
                      P['strong_cool']),

            # Правило 5: Жарко + сухо → умеренное охлаждение
            ctrl.Rule(T['hot'] & H['low'],
                      P['mild_cool']),

            # Правило 6: Ночью снижаем интенсивность (тихий режим)
            ctrl.Rule(TOD['night'] & T['cold'],
                      P['mild_heat']),

            # Правило 7: Утром постепенный прогрев
            ctrl.Rule(TOD['morning'] & T['cold'],
                      P['mild_heat']),

            # Правило 8: Днём при жаре умеренное охлаждение
            ctrl.Rule(TOD['afternoon'] & T['hot'],
                      P['mild_cool']),

            # Правило 9: Вечером комфортный режим
            ctrl.Rule(TOD['evening'] & T['normal'],
                      P['off']),
        ]

    # ------------------------------------------------------------------ #
    #  4. CONTROL SYSTEM                                                  #
    # ------------------------------------------------------------------ #
    def _build_system(self):
        self.thermostat_ctrl = ctrl.ControlSystem(self.rules)
        self.thermostat_sim  = ctrl.ControlSystemSimulation(self.thermostat_ctrl)

    # ------------------------------------------------------------------ #
    #  5. COMPUTE — вычисление мощности                                   #
    # ------------------------------------------------------------------ #
    def compute(self, temperature: float,
                humidity: float,
                time_of_day: float) -> float:
        """
        Вычислить мощность системы.

        Parameters
        ----------
        temperature : float  — температура в °C  (0–40)
        humidity    : float  — влажность в %     (0–100)
        time_of_day : float  — время суток в ч   (0–24)

        Returns
        -------
        float — мощность в % (-100 обогрев … +100 охлаждение)
        """
        # Клэмпинг на допустимые диапазоны
        temperature = float(np.clip(temperature,  0,  40))
        humidity    = float(np.clip(humidity,      0, 100))
        time_of_day = float(np.clip(time_of_day,  0,  24))

        self.thermostat_sim.input['temperature'] = temperature
        self.thermostat_sim.input['humidity']    = humidity
        self.thermostat_sim.input['time_of_day'] = time_of_day

        try:
            self.thermostat_sim.compute()
            return float(self.thermostat_sim.output['power'])
        except Exception:
            return 0.0

    # ------------------------------------------------------------------ #
    #  6. VISUALIZE — графики функций принадлежности                      #
    # ------------------------------------------------------------------ #
    def plot_membership_functions(self, save_path: str = None):
        """Нарисовать функции принадлежности всех переменных."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Функции принадлежности — Нечёткий термостат',
                     fontsize=16, fontweight='bold')

        # ── Температура
        ax = axes[0, 0]
        for term in ['cold', 'normal', 'hot']:
            ax.plot(self.temperature.universe,
                    self.temperature[term].mf,
                    linewidth=2, label=term)
        ax.set_title('Температура (°C)', fontsize=12)
        ax.set_xlabel('°C');  ax.set_ylabel('Степень принадлежности')
        ax.legend();          ax.grid(True, alpha=0.3)
        ax.axvline(x=22, color='gray', linestyle='--',
                   alpha=0.5, label='целевая')

        # ── Влажность
        ax = axes[0, 1]
        for term in ['low', 'medium', 'high']:
            ax.plot(self.humidity.universe,
                    self.humidity[term].mf,
                    linewidth=2, label=term)
        ax.set_title('Влажность (%)', fontsize=12)
        ax.set_xlabel('%');   ax.set_ylabel('Степень принадлежности')
        ax.legend();          ax.grid(True, alpha=0.3)

        # ── Время суток
        ax = axes[1, 0]
        colors = ['navy', 'orange', 'gold', 'coral', 'indigo']
        for term, color in zip(
                ['night', 'morning', 'afternoon', 'evening', 'late_night'],
                colors):
            ax.plot(self.time_of_day.universe,
                    self.time_of_day[term].mf,
                    linewidth=2, label=term, color=color)
        ax.set_title('Время суток (ч)', fontsize=12)
        ax.set_xlabel('Час');  ax.set_ylabel('Степень принадлежности')
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

        # ── Мощность
        ax = axes[1, 1]
        cmap = ['blue', 'cyan', 'green', 'orange', 'red']
        for term, color in zip(
                ['strong_heat', 'mild_heat', 'off',
                 'mild_cool', 'strong_cool'], cmap):
            ax.plot(self.power.universe,
                    self.power[term].mf,
                    linewidth=2, label=term, color=color)
        ax.set_title('Мощность (%)', fontsize=12)
        ax.set_xlabel('% (-обогрев / +охлаждение)')
        ax.set_ylabel('Степень принадлежности')
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
        ax.axvline(x=0, color='black', linestyle='--', alpha=0.5)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ График сохранён: {save_path}")
        plt.show()
        return fig
