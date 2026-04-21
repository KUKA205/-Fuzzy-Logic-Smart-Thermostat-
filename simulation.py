"""
Симуляция работы термостата в течение 24 часов.
Сравнение нечёткой логики с классическим if-else.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from fuzzy_thermostat import FuzzyThermostat
from classic_thermostat import ClassicThermostat


# ─────────────────────────────────────────────────────────────────────────────
#  Реалистичные профили за сутки
# ─────────────────────────────────────────────────────────────────────────────

def generate_day_profile(hours: np.ndarray) -> dict:
    """
    Генерирует реалистичные суточные профили:
    - температура: минимум ночью, максимум днём
    - влажность:   максимум утром, минимум днём
    """
    # Температура: синусоида 15-32°C, пик в 15:00
    temp_base = 23.5
    temp_amp  = 8.5
    temp_phase = (hours - 15) * 2 * np.pi / 24
    temperature = temp_base + temp_amp * np.sin(temp_phase - np.pi / 2)
    # Небольшой шум
    temperature += np.random.normal(0, 0.5, len(hours))
    temperature = np.clip(temperature, 0, 40)

    # Влажность: обратная температуре + утренний пик
    humidity = 75 - 0.8 * (temperature - 15)
    # Утренняя роса (6-9 ч)
    morning_mask = (hours >= 6) & (hours <= 9)
    humidity[morning_mask] += 10
    humidity += np.random.normal(0, 2, len(hours))
    humidity = np.clip(humidity, 20, 95)

    return {'temperature': temperature, 'humidity': humidity}


# ─────────────────────────────────────────────────────────────────────────────
#  Основная симуляция
# ─────────────────────────────────────────────────────────────────────────────

def run_simulation(resolution_minutes: int = 30) -> dict:
    """
    Запускает симуляцию 24 часов с заданным разрешением.
    
    Returns dict со всеми временными рядами.
    """
    np.random.seed(42)

    # Временная шкала
    steps = int(24 * 60 / resolution_minutes)
    hours = np.linspace(0, 24, steps, endpoint=False)

    # Профили входных данных
    profile = generate_day_profile(hours)
    temperatures = profile['temperature']
    humidities   = profile['humidity']

    # Термостаты
    fuzzy_ctrl   = FuzzyThermostat(target_temp=22.0)
    classic_ctrl = ClassicThermostat(target_temp=22.0)

    fuzzy_powers   = []
    classic_powers = []

    print("🔄 Запуск симуляции 24 часов...")
    print(f"   Разрешение: {resolution_minutes} мин | Шагов: {steps}")
    print("-" * 50)

    for i, (h, t, hum) in enumerate(zip(hours, temperatures, humidities)):
        fp = fuzzy_ctrl.compute(t, hum, h)
        cp = classic_ctrl.compute(t, hum, h)

        fuzzy_powers.append(fp)
        classic_powers.append(cp)

        if i % (steps // 12) == 0:  # каждые 2 часа
            print(f"  ⏰ {h:05.2f}h | 🌡️ {t:.1f}°C | 💧 {hum:.0f}% "
                  f"| 🔵 Fuzzy: {fp:+.1f}% | 🔴 Classic: {cp:+.1f}%")

    print("-" * 50)
    print("✅ Симуляция завершена!")

    return {
        'hours':           hours,
        'temperatures':    temperatures,
        'humidities':      humidities,
        'fuzzy_powers':    np.array(fuzzy_powers),
        'classic_powers':  np.array(classic_powers),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Визуализация
# ─────────────────────────────────────────────────────────────────────────────

def plot_simulation(data: dict, save_path: str = None):
    """Подробный график симуляции (4 панели)."""
    hours          = data['hours']
    temperatures   = data['temperatures']
    humidities     = data['humidities']
    fuzzy_powers   = data['fuzzy_powers']
    classic_powers = data['classic_powers']

    fig = plt.figure(figsize=(16, 14))
    gs  = gridspec.GridSpec(4, 1, hspace=0.45)
    xticks = np.arange(0, 25, 2)

    # ── Панель 1: Входные данные ─────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    ax1b = ax1.twinx()

    l1 = ax1.plot(hours, temperatures,
                  color='tomato', linewidth=2.5, label='Температура (°C)')
    l2 = ax1b.plot(hours, humidities,
                   color='steelblue', linewidth=2, linestyle='--',
                   label='Влажность (%)')

    ax1.axhline(y=22, color='green', linestyle=':', linewidth=1.5,
                alpha=0.8, label='Целевая 22°C')
    ax1.fill_between(hours, 20, 24, alpha=0.1, color='green',
                     label='Комфортная зона')

    ax1.set_ylabel('Температура (°C)', color='tomato', fontsize=11)
    ax1b.set_ylabel('Влажность (%)', color='steelblue', fontsize=11)
    ax1.set_title('📊 Входные данные за 24 часа', fontsize=13, fontweight='bold')
    ax1.set_xticks(xticks); ax1.grid(True, alpha=0.3)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', fontsize=9)

    # ── Панель 2: Мощность — нечёткая логика ────────────────────────
    ax2 = fig.add_subplot(gs[1])
    ax2.fill_between(hours, fuzzy_powers, 0,
                     where=(fuzzy_powers > 0),
                     color='red', alpha=0.4, label='Охлаждение')
    ax2.fill_between(hours, fuzzy_powers, 0,
                     where=(fuzzy_powers < 0),
                     color='blue', alpha=0.4, label='Обогрев')
    ax2.plot(hours, fuzzy_powers,
             color='purple', linewidth=2, label='Нечёткая логика')
    ax2.axhline(y=0, color='black', linewidth=0.8)
    ax2.set_ylabel('Мощность (%)', fontsize=11)
    ax2.set_title('🟣 Нечёткая логика — плавное управление',
                  fontsize=13, fontweight='bold')
    ax2.set_ylim(-110, 110)
    ax2.set_xticks(xticks); ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', fontsize=9)

    # ── Панель 3: Мощность — классический if-else ────────────────────
    ax3 = fig.add_subplot(gs[2])
    ax3.fill_between(hours, classic_powers, 0,
                     where=(classic_powers > 0),
                     color='orange', alpha=0.4, label='Охлаждение')
    ax3.fill_between(hours, classic_powers, 0,
                     where=(classic_powers < 0),
                     color='cyan', alpha=0.4, label='Обогрев')
    ax3.step(hours, classic_powers,
             color='darkorange', linewidth=2,
             where='post', label='If-Else')
    ax3.axhline(y=0, color='black', linewidth=0.8)
    ax3.set_ylabel('Мощность (%)', fontsize=11)
    ax3.set_title('🟠 Классический if-else — ступенчатое управление',
                  fontsize=13, fontweight='bold')
    ax3.set_ylim(-110, 110)
    ax3.set_xticks(xticks); ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right', fontsize=9)

    # ── Панель 4: Сравнение ───────────────────────────────────────────
    ax4 = fig.add_subplot(gs[3])
    ax4.plot(hours, np.abs(fuzzy_powers),
             color='purple', linewidth=2.5,
             label=f'Нечёткая логика (ср: {np.mean(np.abs(fuzzy_powers)):.1f}%)')
    ax4.plot(hours, np.abs(classic_powers),
             color='darkorange', linewidth=2, linestyle='--',
             label=f'If-Else (ср: {np.mean(np.abs(classic_powers)):.1f}%)')

    # Шумность — скользящее стд
    window = 5
    fuzzy_std   = [np.std(fuzzy_powers[max(0,i-window):i+window])
                   for i in range(len(hours))]
    classic_std = [np.std(classic_powers[max(0,i-window):i+window])
                   for i in range(len(hours))]
    ax4.fill_between(hours, fuzzy_std, alpha=0.2, color='purple',
                     label='Изменчивость (fuzzy)')
    ax4.fill_between(hours, classic_std, alpha=0.2, color='orange',
                     label='Изменчивость (if-else)')

    ax4.set_xlabel('Время суток (часы)', fontsize=11)
    ax4.set_ylabel('|Мощность| (%)', fontsize=11)
    ax4.set_title('⚖️ Сравнение методов управления',
                  fontsize=13, fontweight='bold')
    ax4.set_xticks(xticks); ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper right', fontsize=9)

    # Подписи времени суток
    for ax in [ax1, ax2, ax3, ax4]:
        ax.axvspan(0,  6,  alpha=0.05, color='navy',  label='_night')
        ax.axvspan(6,  12, alpha=0.05, color='yellow', label='_morning')
        ax.axvspan(12, 18, alpha=0.05, color='orange', label='_afternoon')
        ax.axvspan(18, 22, alpha=0.05, color='coral',  label='_evening')
        ax.axvspan(22, 24, alpha=0.05, color='navy',   label='_night2')

    # Временные метки вверху первого графика
    time_labels = {3: '🌙Ночь', 9: '🌅Утро',
                   15: '☀️День', 20: '🌆Вечер'}
    for x, label in time_labels.items():
        ax1.text(x, ax1.get_ylim()[1] * 0.97, label,
                 ha='center', fontsize=9, color='gray',
                 style='italic')

    plt.suptitle('🌡️ Умный термостат — Симуляция 24 часа',
                 fontsize=16, fontweight='bold', y=1.01)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ График сохранён: {save_path}")
    plt.show()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  Статистика
# ─────────────────────────────────────────────────────────────────────────────

def print_statistics(data: dict):
    fp = data['fuzzy_powers']
    cp = data['classic_powers']
    t  = data['temperatures']

    print("\n" + "=" * 60)
    print("📈 СТАТИСТИКА СИМУЛЯЦИИ")
    print("=" * 60)
    print(f"{'Метрика':<35} {'Нечёткая':>10} {'If-Else':>10}")
    print("-" * 60)

    metrics = [
        ("Средняя |мощность| (%)",
         np.mean(np.abs(fp)),   np.mean(np.abs(cp))),
        ("Макс. мощность (%)",
         np.max(fp),            np.max(cp)),
        ("Мин. мощность (%)",
         np.min(fp),            np.min(cp)),
        ("Стд. отклонение",
         np.std(fp),            np.std(cp)),
        ("Кол-во переключений",
         np.sum(np.abs(np.diff(np.sign(fp))) > 0),
         np.sum(np.abs(np.diff(np.sign(cp))) > 0)),
    ]

    for name, fv, cv in metrics:
        print(f"{name:<35} {fv:>10.2f} {cv:>10.2f}")

    print("-" * 60)
    print(f"{'Темп. профиль:':<35} "
          f"min={t.min():.1f}°C  max={t.max():.1f}°C  "
          f"mean={t.mean():.1f}°C")
    print("=" * 60)

    # Вывод корреляции
    corr = np.corrcoef(fp, cp)[0, 1]
    print(f"\n🔗 Корреляция Fuzzy ↔ If-Else: {corr:.3f}")
    print(f"💡 Нечёткая логика {'ПЛАВНЕЕ' if np.std(fp) < np.std(cp) else 'не плавнее'} "
          f"if-else на {abs(np.std(fp)-np.std(cp)):.1f}%")


# ─────────────────────────────────────────────────────────────────────────────
#  Точка входа
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # 1. Функции принадлежности
    thermostat = FuzzyThermostat()
    thermostat.plot_membership_functions(save_path='membership_functions.png')

    # 2. Симуляция
    data = run_simulation(resolution_minutes=30)

    # 3. Статистика
    print_statistics(data)

    # 4. График
    plot_simulation(data, save_path='simulation_24h.png')
