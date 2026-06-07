import carla
import csv
import math
import time

def main():
    print("Подключение к серверу CARLA...")
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.load_world('Town01')
    
    # Синхронный режим для точности логов
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.1
    world.apply_settings(settings)

    tm = client.get_trafficmanager(8000)
    tm.set_synchronous_mode(True)

    try:
        bp_lib = world.get_blueprint_library()
        bp = bp_lib.filter('vehicle.tesla.model3')[0]
        spawn_points = world.get_map().get_spawn_points()
        
        print("Спавн автомобиля...")
        vehicle = world.try_spawn_actor(bp, spawn_points[0])
        if not vehicle:
            raise RuntimeError("Не удалось заспавнить машину. Перезапустите скрипт.")

        # === КАМЕРА ОТ 3 ЛИЦА (сзади и чуть сверху) ===
        spectator = world.get_spectator()
        
        def update_camera():
            transform = vehicle.get_transform()
            # В CARLA нет get_backward_vector(), поэтому инвертируем forward_vector
            backward_vector = transform.get_forward_vector() * -1.0
            
            # Камера на 5м сзади и 2.5м вверх
            camera_location = transform.location + backward_vector * 5.0 + carla.Location(z=2.5)
            
            # Направляем камеру туда же, куда едет машина, но с легким наклоном вниз (pitch -10)
            # чтобы было лучше видно дорогу и саму машину
            camera_rotation = carla.Rotation(
                pitch=transform.rotation.pitch - 10.0,
                yaw=transform.rotation.yaw,
                roll=transform.rotation.roll
            )
            
            spectator.set_transform(carla.Transform(camera_location, camera_rotation))
        
        update_camera()
        print("Камера установлена: вид от 3 лица (сзади)")

        vehicle.set_autopilot(True, tm.get_port())
        
        # Обратный отсчёт 5 секунд
        print("\n  5 секунд, чтобы переключиться на окно CARLA и нажать Win+Alt+R...")
        for i in range(5, 0, -1):
            print(f"   Старт через {i}...")
            time.sleep(1)
        
        print("\n Автопилот включен. Начинаю запись логов (500 секунд)...")
        
        with open('logs_raw.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['t', 'x', 'y', 'z', 'speed', 'ax', 'ay', 'az', 'throttle', 'brake', 'steer'])
            
            # 10 секунд = 100 тиков (10 * 10)
            for i in range(5000):
                world.tick()
                
                # Обновляем позицию камеры каждый тик, чтобы она ехала за машиной
                update_camera()
                
                loc = vehicle.get_location()
                vel = vehicle.get_velocity()
                acc = vehicle.get_acceleration()
                ctrl = vehicle.get_control()
                
                speed = math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)
                
                w.writerow([
                    round(i * 0.1, 2),
                    round(loc.x, 3), round(loc.y, 3), round(loc.z, 3),
                    round(speed, 3),
                    round(acc.x, 3), round(acc.y, 3), round(acc.z, 3),
                    round(ctrl.throttle, 3), round(ctrl.brake, 3), round(ctrl.steer, 3)
                ])
                
                # Прогресс в консоль каждые 2 секунды
                if i % 20 == 0:
                    print(f"Записано {i/10:.0f} сек | Скорость: {speed:.2f} м/с | Тормоз: {ctrl.brake}")

        print("\n✅ УСПЕХ! Логи сохранены в logs_raw.csv (100 записей)")

    finally:
        print("Очистка сцены...")
        settings.synchronous_mode = False
        world.apply_settings(settings)
        tm.set_synchronous_mode(False)
        if 'vehicle' in locals() and vehicle is not None:
            vehicle.destroy()
        print("Готово.")

if __name__ == '__main__':
    main()