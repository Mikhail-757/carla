import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Настройка шрифтов 
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'DejaVu Sans']

# 1. Читаем сырой лог
df = pd.read_csv('logs_raw.csv')
print(f" Лог загружен: {len(df)} записей | Время: {df['t'].max():.1f}с | Ср.скорость: {df['speed'].mean():.2f} м/с")

# 2. Подготовка данных
# Считаем ГОРИЗОНТАЛЬНОЕ ускорение (исключаем ось Z, так как там гравитация -9.8 м/с²)
df['acc_horizontal'] = np.sqrt(df['ax']**2 + df['ay']**2)

# Находим ВСЕ события торможения (педаль нажата больше чем на 20%)
brake_events = df[df['brake'] > 0.2].copy()
brake_events.to_csv('braking_all.csv', index=False)
print(f"🛑 Событий торможения (brake > 0.2): {len(brake_events)} (сохранено в braking_all.csv)")

# ГРАФИК 1: Скорость и Торможения
plt.figure(figsize=(12, 4))
plt.plot(df['t'], df['speed'], label='Скорость (м/с)', linewidth=1.5, color='blue')
if len(brake_events) > 0:
    plt.scatter(brake_events['t'], brake_events['speed'], color='red', s=30, label='Торможение (brake > 0.2)', zorder=5)
plt.xlabel('Время (с)')
plt.ylabel('Скорость (м/с)')
plt.title('Динамика скорости и точки вмешательства тормоза')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('speed_plot.png', dpi=150)
plt.close()
print(" График скорости сохранён в speed_plot.png")


# ГРАФИК 2: Педали (Газ vs Тормоз)
plt.figure(figsize=(12, 4))
plt.plot(df['t'], df['throttle'], label='Педаль газа (throttle)', color='green', alpha=0.8)
plt.plot(df['t'], df['brake'], label='Педаль тормоза (brake)', color='red', alpha=0.8)
plt.xlabel('Время (с)')
plt.ylabel('Значение (0.0 - 1.0)')
plt.title('Логика работы штатного автопилота CARLA')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('pedals_plot.png', dpi=150)
plt.close()
print(" График педалей сохранён в pedals_plot.png")

# ГРАФИК 3: Продольное ускорение (ИСПРАВЛЕННЫЙ)
# Считаем производную от скорости по времени
df['acc_long'] = df['speed'].diff() / 0.1
df['acc_long'] = df['acc_long'].fillna(0)

# ОГРАНИЧИВАЕМ экстремальные значения (артефакты численного дифференцирования)
# Реальные автомобили не могут тормозить с перегрузкой > 1.5g
df['acc_long_clipped'] = df['acc_long'].clip(-15, 15)

plt.figure(figsize=(12, 4))
plt.plot(df['t'], df['acc_long_clipped'], label='Продольное ускорение (м/с²)', 
         color='purple', alpha=0.7, linewidth=1)
plt.axhline(0, color='black', linewidth=1.5, linestyle='--')

# Подсветка зон торможения
braking_mask = df['acc_long_clipped'] < -1.5
if braking_mask.any():
    plt.scatter(df.loc[braking_mask, 't'], df.loc[braking_mask, 'acc_long_clipped'], 
                color='red', s=30, label='Торможение (< -1.5 м/с²)', zorder=5)

plt.xlabel('Время (с)')
plt.ylabel('Ускорение (м/с²)')
plt.title('Продольное ускорение (ограничено физическими пределами ±15 м/с²)')
plt.ylim(-20, 20)  # Фиксируем ось Y для наглядности
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('acceleration_plot.png', dpi=150)
plt.close()
print(" График ускорения сохранён в acceleration_plot.png")

# ГРАФИК 4: Карта маршрута
plt.figure(figsize=(8, 8))
plt.plot(df['x'], df['y'], 'b-', linewidth=1.5, alpha=0.6, label='Маршрут')
if len(brake_events) > 0:
    plt.scatter(brake_events['x'], brake_events['y'], c='red', s=50, zorder=5, label='Точки торможения', marker='X')
plt.scatter(df['x'].iloc[0], df['y'].iloc[0], c='green', s=100, marker='^', label='Старт', zorder=6)
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.legend()
plt.title('Траектория движения (Town01)')
plt.savefig('route_map.png', dpi=150)
plt.close()
print(" Карта маршрута сохранена в route_map.png")

print("\n  Все 4 графика и braking_all.csv готовы для вставки в отчёт.")