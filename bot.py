import cv2
import requests
import os
from datetime import datetime
import time

# Настройки Telegram
TOKEN = "YOUTOKEN"
CHAT_ID = "YOUCHAT_ID"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# Функция для отправки сообщения в Telegram
def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Ошибка отправки сообщения: {response.text}")

# Функция для отправки фото в Telegram
def send_photo_to_telegram(chat_id, photo_path):
    url = f"{TELEGRAM_API}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': chat_id}
        response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print("Фото успешно отправлено в Telegram!")
    else:
        print(f"Ошибка отправки: {response.text}")

# Функция для отправки видео в Telegram
def send_video_to_telegram(chat_id, video_path):
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # Размер в МБ
    if file_size > 50:
        send_message(chat_id, f"Ошибка: видео ({file_size:.2f} МБ) превышает лимит Telegram (50 МБ)")
        return
    
    url = f"{TELEGRAM_API}/sendVideo"
    with open(video_path, 'rb') as video:
        files = {'video': video}
        data = {'chat_id': chat_id}
        response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print("Видео успешно отправлено в Telegram!")
    else:
        print(f"Ошибка отправки: {response.text}")

# Функция для съемки фото
def take_photo(chat_id):
    cap = cv2.VideoCapture(0)  # 0 - первая подключенная камера
    if not cap.isOpened():
        send_message(chat_id, "Ошибка: не удалось открыть веб-камеру")
        return

    ret, frame = cap.read()  # Считываем кадр
    if ret:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_path = f"photo_{timestamp}.jpg"
        cv2.imwrite(photo_path, frame)  # Сохраняем фото
        print(f"Фото сохранено как {photo_path}")
        
        # Отправляем фото в Telegram
        send_photo_to_telegram(chat_id, photo_path)
        
        # Удаляем файл после отправки
        os.remove(photo_path)
    else:
        send_message(chat_id, "Ошибка: не удалось сделать фото")
    
    cap.release()  # Освобождаем камеру

# Функция для записи видео
def record_video(chat_id, duration=10):
    cap = cv2.VideoCapture(0)  # 0 - первая подключенная камера
    if not cap.isOpened():
        send_message(chat_id, "Ошибка: не удалось открыть веб-камеру")
        return

    # Настройки видео (формат .mp4)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Кодек для .mp4
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = f"video_{timestamp}.mp4"
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))  # 20 FPS, разрешение 640x480

    send_message(chat_id, f"Запись видео началась на {duration} секунд...")
    start_time = cv2.getTickCount()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            send_message(chat_id, "Ошибка: не удалось записать кадр")
            break
        
        out.write(frame)  # Записываем кадр в видео
        
        # Проверяем длительность записи
        elapsed_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
        if elapsed_time > duration:
            break

    # Завершаем запись
    cap.release()
    out.release()
    print(f"Видео сохранено как {video_path}")
    
    # Отправляем видео в Telegram
    send_message(chat_id, "Отправляю видео...")
    send_video_to_telegram(chat_id, video_path)
    
    # Удаляем файл после отправки
    os.remove(video_path)

# Функция для получения обновлений от Telegram
def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения обновлений: {response.text}")
        return None

# Основной цикл бота
def main():
    print("Бот запущен. Отправь /start в Telegram для начала.")
    offset = None
    
    while True:
        updates = get_updates(offset)
        if updates and updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                offset = update["update_id"] + 1  # Обновляем offset
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].lower()

                    # Обработка команд
                    if text == "/start":
                        send_message(chat_id, "Привет! Я бот для управления веб-камерой.\n"
                                             "Команды:\n/photo - сделать фото\n/video - записать видео (10 сек)")
                    elif text == "/photo":
                        send_message(chat_id, "Делаю фото...")
                        take_photo(chat_id)
                    elif text == "/video":
                        send_message(chat_id, "Начинаю запись видео...")
                        record_video(chat_id, duration=10)
                    else:
                        send_message(chat_id, "Неизвестная команда. Используй /photo или /video.")
        
        time.sleep(1)  # Задержка для снижения нагрузки

if __name__ == "__main__":
    main()