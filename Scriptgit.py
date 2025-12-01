import subprocess
import time
import requests

TARGET_IP = ""

BOT_TOKEN = ""
CHAT_ID = ""

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_state = None
last_update_id = 0  # для отслеживания новых сообщений


def send_tg(text, chat_id=CHAT_ID):
    try:
        requests.get(
            f"{TELEGRAM_API}/sendMessage",
            params={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)


def is_device_online():
    """Возвращает True если устройство есть в ARP-таблице."""
    result = subprocess.run("arp -a", shell=True, capture_output=True, text=True)
    return TARGET_IP in result.stdout


def check_now():
    """Одноразовая проверка — в сети ли устройство."""
    online = is_device_online()
    if online:
        print(f"[CHECK] {TARGET_IP} — В СЕТИ")
    else:
        print(f"[CHECK] {TARGET_IP} — НЕТ В СЕТИ")
    return online


def monitor():
    """Основной мониторинг устройства и отправка событий в Telegram."""
    global last_state
    print("[START] Мониторинг устройства...")
    while True:
        online = is_device_online()
        if online != last_state:  # состояние изменилось
            if online:
                msg = f"📲 Телефон {TARGET_IP} подключился к Wi-Fi!"
                print("[EVENT] Подключено")
            else:
                msg = f"❌ Телефон {TARGET_IP} пропал из сети!"
                print("[EVENT] Отключено")
            send_tg(msg)
            last_state = online
        time.sleep(5)


def check_commands():
    """Проверяет Telegram на новые команды."""
    global last_update_id
    try:
        resp = requests.get(f"{TELEGRAM_API}/getUpdates", params={"timeout": 10, "offset": last_update_id+1})
        data = resp.json()

        for item in data["result"]:
            last_update_id = item["update_id"]
            msg = item.get("message")
            if not msg:
                continue
            text = msg.get("text")
            chat_id = msg["chat"]["id"]

            if text == "/status":
                online = is_device_online()
                if online:
                    send_tg(f"📲 {TARGET_IP} подключено к сети", chat_id)
                else:
                    send_tg(f"❌ {TARGET_IP} не в сети", chat_id)

    except Exception as e:
        print("Ошибка проверки команд:", e)


# ---------- Запуск ----------
if __name__ == "__main__":
    import threading

    # 1. Мониторинг устройства в отдельном потоке
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    # 2. Проверка команд бота в основном потоке
    print("[START] Проверка команд Telegram")
    while True:
        check_commands()
        time.sleep(2)
