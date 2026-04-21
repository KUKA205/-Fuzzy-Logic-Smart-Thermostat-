# 🌡️ Fuzzy Logic Smart Thermostat | Умный термостат на нечёткой логике

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 📋 Описание
Умный термостат на основе нечёткой логики (Fuzzy Logic).
Система учитывает температуру, влажность и время суток
для оптимального управления мощностью обогрева/охлаждения.

## 🚀 Быстрый старт

### Установка
git clone https://github.com/yourusername/fuzzy-thermostat.git
cd fuzzy-thermostat
pip install -r requirements.txt

### Запуск симуляции
python simulation.py

### Запуск веб-приложения
streamlit run app.py

## 🧠 Нечёткая логика
- **Входные переменные**: температура (0-40°C), влажность (0-100%), время суток (0-24ч)
- **Выходная переменная**: мощность системы (-100% до +100%)
- **9 правил** для управления

## 📊 Сравнение
| Метод | Плавность | Адаптивность | Сложность |
|-------|-----------|--------------|-----------|
| Нечёткая логика | ✅ Высокая | ✅ Высокая | 🔶 Средняя |
| If-Else | ❌ Ступенчатая | ❌ Низкая | ✅ Низкая |

## 📁 Файлы
- `fuzzy_thermostat.py` — ядро нечёткой логики
- `simulation.py` — симуляция 24 часов
- `classic_thermostat.py` — классический if-else
- `app.py` — интерактивный Streamlit интерфейс
