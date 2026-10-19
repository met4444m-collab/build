#!/usr/bin/env python3
"""SafeGuard: сторож папки загрузок.
Новый файл -> chmod -x (блок запуска) + уведомление с кнопками.
Файл в автозагрузке -> отдельное предупреждение.
"""
import os
import subprocess
import time
import hashlib
import sys

DOWNLOADS = os.path.expanduser("~/Downloads")
AUTOSTART_DIRS = [
    os.path.expanduser("~/.config/autostart"),
    os.path.expanduser("~/.local/share/autostart"),
]
SEEN = set()


def notify(title, body, actions):
    """notify-send с кнопками. Возвращает выбранное действие или ''."""
    cmd = ["notify-send", "--app-name=SafeGuard", "--urgency=critical"]
    for a in actions:
        cmd.append("--action=" + a)
    cmd += [title, body]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=120).strip()
        return out
    except Exception:
        return ""


def scan(path):
    try:
        out = subprocess.check_output(["clamscan", "--no-summary", path], text=True, timeout=300)
        return "OK" if "FOUND" not in out else out.strip()
    except Exception as e:
        return "scan error: %s" % e


def handle(path):
    name = os.path.basename(path)
    # снимаем право на выполнение — файл не запустится двойным кликом
    try:
        os.chmod(path, os.stat(path).st_mode & ~0o111)
    except Exception:
        pass
    choice = notify("SafeGuard: новый файл", name,
                    ["open=Открыть", "scan=Сканировать", "delete=Удалить", "close=Закрыть"])
    if choice == "open":
        os.chmod(path, os.stat(path).st_mode | 0o100)
        subprocess.Popen(["xdg-open", path])
    elif choice == "scan":
        res = scan(path)
        notify("SafeGuard: скан", name + "\n" + res, ["ok=OK"])
    elif choice == "delete":
        try:
            os.remove(path)
        except Exception:
            pass


def main():
    os.makedirs(DOWNLOADS, exist_ok=True)
    while True:
        try:
            for fn in os.listdir(DOWNLOADS):
                p = os.path.join(DOWNLOADS, fn)
                if not os.path.isfile(p):
                    continue
                key = (p, os.path.getmtime(p), os.path.getsize(p))
                if key in SEEN:
                    continue
                SEEN.add(key)
                # автозагрузка?
                if any(p.startswith(d + os.sep) for d in AUTOSTART_DIRS):
                    notify("SafeGuard: АВТОЗАГРУЗКА",
                           fn + " — файл в автозагрузке!",
                           ["delete=Удалить", "scan=Сканировать", "close=Закрыть"])
                else:
                    handle(p)
        except Exception:
            pass
        time.sleep(3)


if __name__ == "__main__":
    main()