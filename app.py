"""
Streamlit приложение — Умный термостат на нечёткой логике.
Запуск: streamlit run app.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from fuzzy_thermostat import FuzzyThermostat
from classic_thermostat import ClassicThermostat
from simulation import run_simulation, plot_simulation, print_statistics

# ─────────────────────────────────────────────────────────────────────────────
#  Конфигурация страницы
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="🌡️ Умный термостат",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Инициализация термостатов (кэшируем чтобы не пересоздавать)
@st.cache_resource
def get_thermostats():
    return FuzzyThermostat(target_temp=22.0), ClassicThermostat(target_temp=22.0)

fuzzy_ctrl, classic_ctrl = get_thermostats()


# ─────────────────────────────────────────────────────────────────────────────
#  ЗАГОЛОВОК
# ─────────────────────────────────────────────────────────────────────────────

st.title("🌡️ Умный термостат — Нечёткая логика")
st.markdown("""
> Система управления климатом на основе **нечёткой логики** (Fuzzy Logic).  
> Входы: температура, влажность, время суток → Выход: мощность системы.
""")

# ─────────────────────────────────────────────────────────────────────────────
#  САЙДБАР — слайдеры
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.header("⚙️ Параметры")
st.sidebar.markdown("---")

st.sidebar.subheader("🌡️ Входные данные")

temperature = st.sidebar.slider(
    "Температура (°C)",
    min_value=0.0, max_value=40.0,
    value=25.0, step=0.5,
    help="Текущая температура в помещении"
)

humidity = st.sidebar.slider(
    "Влажность (%)",
    min_value=0, max_value=100,
    value=60, step=1,
    help="Относительная влажность воздуха"
)

time_of_day = st.sidebar.slider(
    "Время суток (ч)",
    min_value=0.0, max_value=24.0,
    value=14.0, step=0.5,
    help="Текущее время (0=полночь, 12=полдень)"
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Целевая температура")
target_temp = st.sidebar.number_input(
    "Целевая температура (°C)",
    min_value=15.0, max_value=30.0,
    value=22.0, step=0.5
)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Симуляция")
sim_resolution = st.sidebar.selectbox(
    "Разрешение симуляции",
    options=[15, 30, 60],
    index=1,
    help="Шаг симуляции в минутах"
)
run_sim = st.sidebar.button("▶️ Запустить симуляцию 24ч", type="primary")


# ─────────────────────────────────────────────────────────────────────────────
#  ВЫЧИСЛЕНИЕ
# ─────────────────────────────────────────────────────────────────────────────

fuzzy_power   = fuzzy_ctrl.compute(temperature, humidity, time_of_day)
classic_power = classic_ctrl.compute(temperature, humidity, time_of_day)


# ─────────────────────────────────────────────────────────────────────────────
#  ТЕКУЩЕЕ СОСТОЯНИЕ (вверху)
# ─────────────────────────────────────────────────────────────────────────────

def power_to_mode(power: float) -> tuple:
    """Возвращает (emoji, описание, цвет)."""
    if power < -60:
        return "🔥", "Сильный обогрев",   "#ff4444"
    elif power < -20:
        return "🌡️", "Умеренный обогрев", "#ff8844"
    elif power < 20:
        return "✅", "Комфортный режим",   "#44bb44"
    elif power < 60:
        return "❄️", "Умеренное охлаждение", "#4488ff"
    else:
        return "🧊", "Сильное охлаждение",  "#0044ff"

f_emoji, f_mode, f_color = power_to_mode(fuzzy_power)
c_emoji, c_mode, c_color = power_to_mode(classic_power)

# Время суток
def get_time_label(h):
    if h < 6 or h >= 22:  return "🌙 Ночь"
    elif h < 12:           return "🌅 Утро"
    elif h < 18:           return "☀️ День"
    else:                  return "🌆 Вечер"

st.subheader("📍 Текущее состояние")

col1, col2, col3, col4 = st.columns(4)
with col1:
    delta = temperature - target_temp
    st.metric("🌡️ Температура", f"{temperature}°C",
              delta=f"{delta:+.1f}°C от цели",
              delta_color="inverse")
with col2:
    hum_status = "🟢" if 40 <= humidity <= 70 else "🟡"
    st.metric(f"{hum_status} Влажность", f"{humidity}%")
with col3:
    st.metric("🕐 Время суток",
              f"{int(time_of_day):02d}:{int((time_of_day%1)*60):02d}",
              delta=get_time_label(time_of_day))
with col4:
    st.metric("🎯 Цель", f"{target_temp}°C")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
#  СРАВНЕНИЕ МЕТОДОВ
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("⚖️ Сравнение методов управления")

col_fuzzy, col_classic = st.columns(2)

with col_fuzzy:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px; border-radius: 12px; color: white;'>
        <h3 style='margin:0; color:white;'>🟣 Нечёткая логика</h3>
        <h1 style='margin:10px 0; font-size: 3em; color:white;'>
            {fuzzy_power:+.1f}%
        </h1>
        <p style='margin:0; font-size: 1.2em;'>{f_emoji} {f_mode}</p>
        <hr style='border-color: rgba(255,255,255,0.3);'>
        <p style='margin:0; opacity:0.8;'>
            Плавное управление на основе 9 правил<br>
            Учитывает все факторы одновременно
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_classic:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 20px; border-radius: 12px; color: white;'>
        <h3 style='margin:0; color:white;'>🔴 Классический If-Else</h3>
        <h1 style='margin:10px 0; font-size: 3em; color:white;'>
            {classic_power:+.1f}%
        </h1>
        <p style='margin:0; font-size: 1.2em;'>{c_emoji} {c_mode}</p>
        <hr style='border-color: rgba(255,255,255,0.3);'>
        <p style='margin:0; opacity:0.8;'>
            Пороговая логика — ступенчатые переключения<br>
            Простые правила без нюансов
        </p>
    </div>
    """, unsafe_allow_html=True)

# Разница
diff = fuzzy_power - classic_power
st.markdown(f"""
<div style='background: #f0f2f6; padding: 15px; border-radius: 8px;
            margin-top: 15px; text-align: center;'>
    <b>Разница между методами: {diff:+.1f}%</b>  |  
    Нечёткая логика {'мягче' if abs(fuzzy_power) < abs(classic_power) else 'агрессивнее'} на {abs(diff):.1f}%
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
#  ИНДИКАТОР МОЩНОСТИ
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("🎚️ Визуальный индикатор мощности")

def make_power_gauge(power: float, title: str) -> plt.Figure:
    fig, ax = plt.subplots(1, 1, figsize=(8, 2))

    # Шкала
    ax.barh(0, 200, left=-100, height=0.6,
            color='lightgray', alpha=0.3, edgecolor='gray')

    # Зоны
    ax.barh(0, 100, left=-100, height=0.6, color='#4488ff', alpha=0.2)
    ax.barh(0, 100, left=0,    height=0.6, color='#ff4444', alpha=0.2)

    # Значение
    color = '#0044ff' if power < 0 else '#ff0000'
    ax.barh(0, power, left=0, height=0.5, color=color, alpha=0.8)

    # Центральная линия
    ax.axvline(x=0, color='black', linewidth=2)

    # Метка
    ax.text(power + (3 if power >= 0 else -3), 0,
            f'{power:+.1f}%',
            ha='left' if power >= 0 else 'right',
            va='center', fontsize=14, fontweight='bold', color=color)

    ax.set_xlim(-110, 110)
    ax.set_ylim(-0.5, 0.5)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('← Обогрев | Охлаждение →')
    ax.set_yticks([])
    ax.axvline(x=-100, color='blue', linewidth=1, alpha=0.5)
    ax.axvline(x= 100, color='red',  linewidth=1, alpha=0.5)
    ax.text(-100, -0.45, 'Макс.\nобогрев',
            ha='center', fontsize=7, color='blue', alpha=0.7)
    ax.text( 100, -0.45, 'Макс.\nохлажд.',
            ha='center', fontsize=7, color='red',  alpha=0.7)
    ax.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    return fig

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.pyplot(make_power_gauge(fuzzy_power, "🟣 Нечёткая логика"))
with col_g2:
    st.pyplot(make_power_gauge(classic_power, "🔴 Классический If-Else"))

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
#  ФУНКЦИИ ПРИНАДЛЕЖНОСТИ
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📊 Функции принадлежности (нечёткие множества)", expanded=False):
    fig = fuzzy_ctrl.plot_membership_functions()
    st.pyplot(fig)
    st.markdown("""
    **Как читать:** Каждая линия показывает, насколько входное значение 
    принадлежит данному нечёткому множеству (0=не принадлежит, 1=полностью).
    """)

# ─────────────────────────────────────────────────────────────────────────────
#  ПРАВИЛА
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📋 Правила нечёткой логики", expanded=False):
    rules_data = {
        "№": list(range(1, 10)),
        "Условие": [
            "Холодно И Сухо",
            "Холодно И Влажно",
            "Нормальная температура",
            "Жарко И Влажно",
            "Жарко И Сухо",
            "Ночь И Холодно",
            "Утро И Холодно",
            "День И Жарко",
            "Вечер И Нормально",
        ],
        "Результат": [
            "Сильный обогрев (-100%)",
            "Умеренный обогрев (-35%)",
            "Выключено (0%)",
            "Сильное охлаждение (+100%)",
            "Умеренное охлаждение (+35%)",
            "Умеренный обогрев (-35%)",
            "Умеренный обогрев (-35%)",
            "Умеренное охлаждение (+35%)",
            "Выключено (0%)",
        ],
        "Логика": [
            "Холодный воздух быстро теряет тепло",
            "Влага снижает теплоотдачу",
            "Ничего не делаем",
            "Жарко + влажно = некомфортно",
            "Жарко, но сухой воздух легче",
            "Ночью тишина, умеренно",
            "Утренний прогрев",
            "Пиковая жара днём",
            "Вечером комфортно",
        ]
    }
    st.table(rules_data)
    st.markdown("""
    > **Классический if-else** использует жёсткие пороги → ступенчатые переключения  
    > **Нечёткая логика** комбинирует правила плавно → нет резких скачков
    """)

# ─────────────────────────────────────────────────────────────────────────────
#  СИМУЛЯЦИЯ 24 ЧАСА
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("⏱️ Симуляция 24 часа")

if run_sim:
    with st.spinner(f"🔄 Симуляция ({sim_resolution} мин/шаг)..."):
        data = run_simulation(resolution_minutes=sim_resolution)

    # Статистика
    fp = data['fuzzy_powers']
    cp = data['classic_powers']

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Ср. |мощность| Fuzzy",
                  f"{np.mean(np.abs(fp)):.1f}%")
    with col_s2:
        st.metric("Ср. |мощность| If-Else",
                  f"{np.mean(np.abs(cp)):.1f}%")
    with col_s3:
        st.metric("Стд. Fuzzy", f"{np.std(fp):.1f}%")
    with col_s4:
        st.metric("Стд. If-Else", f"{np.std(cp):.1f}%")

    # График симуляции
    fig_sim = plot_simulation(data)
    st.pyplot(fig_sim)

    # Скачать данные
    import io
    buf = io.BytesIO()
    fig_sim.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.download_button(
        "⬇️ Скачать график",
        data=buf,
        file_name="simulation_24h.png",
        mime="image/png"
    )
else:
    st.info("👆 Нажмите **▶️ Запустить симуляцию 24ч** в боковом меню")

# ─────────────────────────────────────────────────────────────────────────────
#  СРАВНЕНИЕ В ТАБЛИЦЕ
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
with st.expander("📊 Детальное сравнение методов", expanded=True):
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("### 🟣 Нечёткая логика")
        st.markdown("""
        | Характеристика | Значение |
        |---|---|
        | **Плавность** | ✅ Непрерывная |
        | **Адаптивность** | ✅ Высокая |
        | **Правил** | 9 нечётких |
        | **Переключения** | Плавные |
        | **Учёт контекста** | ✅ Все факторы |
        | **Сложность** | 🔶 Средняя |
        | **Настройка** | Экспертные знания |
        """)

    with col_t2:
        st.markdown("### 🔴 Классический If-Else")
        st.markdown("""
        | Характеристика | Значение |
        |---|---|
        | **Плавность** | ❌ Ступенчатая |
        | **Адаптивность** | ❌ Низкая |
        | **Правил** | 5 порогов |
        | **Переключения** | Резкие |
        | **Учёт контекста** | 🔶 Частичный |
        | **Сложность** | ✅ Низкая |
        | **Настройка** | Простые пороги |
        """)

# ─────────────────────────────────────────────────────────────────────────────
#  ФУТЕР
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    🌡️ <b>Умный термостат на нечёткой логике</b><br>
    Библиотеки: scikit-fuzzy · matplotlib · streamlit · numpy<br>
    <small>Алгоритм: Mamdani Fuzzy Inference System</small>
</div>
""", unsafe_allow_html=True)
