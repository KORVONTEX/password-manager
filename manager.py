import os
import json
import base64
import sys
import random
import string
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    pyperclip = None
    PYPERCLIP_AVAILABLE = False

try:
    from colorama import init, Fore, Style
    init()
    COLORS_AVAILABLE = True
except ImportError:
    init = None
    Fore = None
    Style = None
    COLORS_AVAILABLE = False

DATA_FILE = "passwords.enc"
SALT_FILE = "salt.bin"


def clear_screen():
    os.system('cls' if sys.platform == 'win32' else 'clear')


def color_text(text, color='white'):
    if not COLORS_AVAILABLE:
        return text

    colors = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE,
        'magenta': Fore.MAGENTA
    }
    return f"{colors.get(color, Fore.WHITE)}{text}{Style.RESET_ALL}"


def get_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt(data, password, salt):
    key = get_key(password, salt)
    f = Fernet(key)
    return f.encrypt(json.dumps(data, ensure_ascii=False, indent=2).encode())


def decrypt(encrypted, password, salt):
    key = get_key(password, salt)
    f = Fernet(key)
    return json.loads(f.decrypt(encrypted).decode())


def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    return password


def search_sites(passwords, query):
    query_lower = query.lower()
    results = []
    for site in passwords.keys():
        if query_lower in site.lower():
            results.append(site)
    return results


def export_passwords(passwords):
    filename = "passwords_export.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)
    return filename


def import_passwords(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def change_master_password(passwords, old_master, old_salt, new_master):
    new_salt = os.urandom(16)
    encrypted = encrypt(passwords, new_master, new_salt)

    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)
    with open(SALT_FILE, "wb") as f:
        f.write(new_salt)

    return new_salt


def show_statistics(passwords):
    total = len(passwords)
    if total == 0:
        return 0, 0

    weak_count = 0
    for site, data in passwords.items():
        pwd = data.get('password', '')
        if len(pwd) < 8:
            weak_count += 1

    return total, weak_count


def backup_passwords(passwords):
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, os.path.join(backup_dir, DATA_FILE))
    if os.path.exists(SALT_FILE):
        shutil.copy2(SALT_FILE, os.path.join(backup_dir, SALT_FILE))

    return backup_dir


def main():
    clear_screen()

    print(color_text("=" * 50, 'cyan'))
    print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
    print(color_text("   (AES-256)", 'yellow'))
    print(color_text("=" * 50, 'cyan'))

    if not os.path.exists(DATA_FILE):
        print(color_text("\n🔐 ПЕРВЫЙ ЗАПУСК!", 'green'))
        print(color_text("Придумайте мастер-пароль. ОН НЕ ВОССТАНАВЛИВАЕТСЯ!\n", 'red'))

        master = input("Мастер-пароль: ")
        master2 = input("Повторите мастер-пароль: ")

        if master != master2:
            print(color_text("\n❌ Пароли не совпадают!", 'red'))
            input(color_text("\nНажмите Enter для выхода...", 'white'))
            return

        salt = os.urandom(16)
        encrypted = encrypt({}, master, salt)

        with open(DATA_FILE, "wb") as f:
            f.write(encrypted)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)

        clear_screen()
        print(color_text("=" * 50, 'cyan'))
        print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
        print(color_text("   (AES-256)", 'yellow'))
        print(color_text("=" * 50, 'cyan'))
        print(color_text("\n✅ Мастер-пароль создан!", 'green'))
        print(color_text("Файлы: passwords.enc и salt.bin", 'green'))
        print(color_text("\n🔓 Вход выполнен автоматически!", 'green'))
        input(color_text("\nНажмите Enter для продолжения...", 'white'))
        passwords = {}

    else:
        print(color_text("\n🔐 ВХОД", 'cyan'))
        master = input("Мастер-пароль: ")

        with open(DATA_FILE, "rb") as f:
            encrypted = f.read()
        with open(SALT_FILE, "rb") as f:
            salt = f.read()

        try:
            passwords = decrypt(encrypted, master, salt)
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n✅ Вход выполнен!", 'green'))
            input(color_text("\nНажмите Enter для продолжения...", 'white'))
        except Exception:
            print(color_text("\n❌ НЕВЕРНЫЙ МАСТЕР-ПАРОЛЬ!", 'red'))
            input(color_text("\nНажмите Enter для выхода...", 'white'))
            return

    while True:
        clear_screen()

        print(color_text("=" * 50, 'cyan'))
        print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
        print(color_text("   (AES-256)", 'yellow'))
        print(color_text("=" * 50, 'cyan'))

        total, weak = show_statistics(passwords)
        print(color_text(f"\n📊 Всего паролей: {total}  |  Слабых: {weak}", 'cyan'))

        print(color_text("\n" + "-" * 40, 'cyan'))
        print(color_text("   ГЛАВНОЕ МЕНЮ", 'yellow'))
        print(color_text("-" * 40, 'cyan'))
        print(color_text(" 1. Добавить пароль", 'white'))
        print(color_text(" 2. Показать все сайты", 'white'))
        print(color_text(" 3. Найти пароль", 'white'))
        print(color_text(" 4. Удалить пароль", 'white'))
        print(color_text(" 5. Сгенерировать пароль", 'white'))
        print(color_text(" 6. Сменить мастер-пароль", 'white'))
        print(color_text(" 7. Экспорт/Импорт паролей", 'white'))
        print(color_text(" 8. Статистика и резервное копирование", 'white'))
        print(color_text(" 9. Выйти", 'white'))
        print(color_text("-" * 40, 'cyan'))

        choice = input(color_text("\nВыберите действие (1-9): ", 'cyan'))

        if choice == "1":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- ДОБАВЛЕНИЕ ПАРОЛЯ ---\n", 'green'))

            site = input("Название сайта: ").strip()
            if site in passwords:
                print(color_text("\n⚠️ Такой сайт уже есть!", 'yellow'))
                input(color_text("\nНажмите Enter для возврата в меню...", 'white'))
                continue

            login = input("Логин: ").strip()
            pwd = input("Пароль: ").strip()

            if len(pwd) < 8:
                print(color_text("\n⚠️ Слабый пароль! (меньше 8 символов)", 'yellow'))
                confirm = input("Всё равно сохранить? (д/н): ")
                if confirm.lower() != 'д':
                    continue

            passwords[site] = {"login": login, "password": pwd}

            encrypted = encrypt(passwords, master, salt)
            with open(DATA_FILE, "wb") as f:
                f.write(encrypted)

            print(color_text(f"\n✅ Пароль для '{site}' сохранён!", 'green'))
            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "2":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- СОХРАНЁННЫЕ САЙТЫ ---\n", 'green'))

            if not passwords:
                print(color_text("📭 Нет сохранённых паролей", 'yellow'))
            else:
                for i, site in enumerate(passwords.keys(), 1):
                    pwd = passwords[site].get('password', '')
                    strength = "🔴" if len(pwd) < 8 else "🟢"
                    print(color_text(f"  {i}. {strength} {site}", 'white'))

            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "3":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- ПОИСК ПАРОЛЯ ---\n", 'green'))

            query = input("Введите название сайта или его часть: ").strip()

            if not query:
                print(color_text("\n❌ Пустой запрос!", 'red'))
                input(color_text("\nНажмите Enter...", 'white'))
                continue

            results = search_sites(passwords, query)

            if not results:
                print(color_text(f"\n❌ Сайты по запросу '{query}' не найдены", 'red'))
                input(color_text("\nНажмите Enter для возврата в меню...", 'white'))
                continue

            if len(results) > 1:
                print(color_text(f"\n🔍 Найдено несколько сайтов:", 'cyan'))
                for i, site in enumerate(results, 1):
                    print(color_text(f"  {i}. {site}", 'white'))
                print(color_text(f"\n 0. Отмена", 'white'))

                idx = input(color_text("\nВыберите номер: ", 'cyan'))
                if idx == "0" or not idx.isdigit():
                    continue
                idx = int(idx) - 1
                if idx < 0 or idx >= len(results):
                    print(color_text("❌ Неверный выбор!", 'red'))
                    input(color_text("\nНажмите Enter...", 'white'))
                    continue
                site = results[idx]
            else:
                site = results[0]

            print(color_text(f"\n🔓 ДАННЫЕ ДЛЯ {site.upper()}", 'magenta'))
            print(color_text("-" * 40, 'cyan'))
            print(color_text(f"   Логин:  {passwords[site]['login']}", 'white'))
            print(color_text(f"   Пароль: {passwords[site]['password']}", 'white'))

            pwd_len = len(passwords[site]['password'])
            if pwd_len < 8:
                print(color_text(f"   ⚠️ Слабый пароль (меньше 8 символов)", 'yellow'))
            elif pwd_len < 12:
                print(color_text(f"   ✅ Средний пароль", 'green'))
            else:
                print(color_text(f"   🔒 Сильный пароль!", 'green'))

            print(color_text("-" * 40, 'cyan'))

            if PYPERCLIP_AVAILABLE:
                copy_choice = input(color_text("\nСкопировать пароль в буфер обмена? (д/н): ", 'cyan'))
                if copy_choice.lower() == 'д':
                    pyperclip.copy(passwords[site]['password'])
                    print(color_text("✅ Пароль скопирован! Можно вставить (Ctrl+V)", 'green'))
            else:
                print(color_text("\n⚠️ Для копирования установите: pip install pyperclip", 'yellow'))

            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "4":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- УДАЛЕНИЕ ПАРОЛЯ ---\n", 'red'))

            site = input("Название сайта для удаления: ").strip()

            if site in passwords:
                confirm = input(color_text(f"Удалить '{site}'? (д/н): ", 'yellow'))
                if confirm.lower() == 'д':
                    del passwords[site]
                    encrypted = encrypt(passwords, master, salt)
                    with open(DATA_FILE, "wb") as f:
                        f.write(encrypted)
                    print(color_text(f"\n🗑️ Пароль для '{site}' удалён!", 'green'))
                else:
                    print(color_text("\nОтменено", 'yellow'))
            else:
                print(color_text(f"\n❌ Сайт '{site}' не найден", 'red'))

            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "5":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- ГЕНЕРАТОР ПАРОЛЕЙ ---\n", 'green'))

            print(color_text("Рекомендации:", 'cyan'))
            print(color_text("  • 12-16 символов для обычных сайтов", 'white'))
            print(color_text("  • 20+ символов для важных аккаунтов", 'white'))

            try:
                length = int(input("\nДлина пароля (по умолчанию 12): ") or 12)
                if length < 6:
                    length = 12
                    print(color_text("Минимум 6 символов, установлено 12", 'yellow'))
            except:
                length = 12

            generated = generate_password(length)
            print(color_text(f"\n🔑 Сгенерированный пароль: ", 'cyan'))
            print(color_text(f"   {generated}", 'yellow'))

            if length < 8:
                print(color_text(f"   ⚠️ Слабый", 'yellow'))
            elif length < 12:
                print(color_text(f"   ✅ Средний", 'green'))
            else:
                print(color_text(f"   🔒 Сильный", 'green'))

            if PYPERCLIP_AVAILABLE:
                copy_choice = input(color_text("\nСкопировать пароль в буфер обмена? (д/н): ", 'cyan'))
                if copy_choice.lower() == 'д':
                    pyperclip.copy(generated)
                    print(color_text("✅ Пароль скопирован!", 'green'))

            save_choice = input(color_text("\nСохранить этот пароль для сайта? (д/н): ", 'cyan'))
            if save_choice.lower() == 'д':
                site = input("Название сайта: ").strip()
                login = input("Логин: ").strip()
                passwords[site] = {"login": login, "password": generated}
                encrypted = encrypt(passwords, master, salt)
                with open(DATA_FILE, "wb") as f:
                    f.write(encrypted)
                print(color_text(f"\n✅ Пароль для '{site}' сохранён!", 'green'))

            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "6":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- СМЕНА МАСТЕР-ПАРОЛЯ ---\n", 'yellow'))

            print(color_text("ВНИМАНИЕ! Это перешифрует все ваши пароли новым ключом.\n", 'red'))

            old_check = input("Введите ТЕКУЩИЙ мастер-пароль для подтверждения: ")

            try:
                decrypt(encrypted, old_check, salt)
            except:
                print(color_text("\n❌ Неверный текущий мастер-пароль!", 'red'))
                input(color_text("\nНажмите Enter...", 'white'))
                continue

            new_master = input("\nНовый мастер-пароль: ")
            new_master2 = input("Повторите новый мастер-пароль: ")

            if new_master != new_master2:
                print(color_text("\n❌ Пароли не совпадают!", 'red'))
                input(color_text("\nНажмите Enter...", 'white'))
                continue

            if len(new_master) < 6:
                print(color_text("\n⚠️ Слабый мастер-пароль! (меньше 6 символов)", 'yellow'))
                confirm = input("Всё равно использовать? (д/н): ")
                if confirm.lower() != 'д':
                    continue

            salt = change_master_password(passwords, master, salt, new_master)
            master = new_master

            print(color_text("\n✅ Мастер-пароль успешно изменён!", 'green'))
            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "7":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- ЭКСПОРТ/ИМПОРТ ---\n", 'green'))
            print(color_text(" 1. Экспорт паролей (НЕЗАШИФРОВАННЫЙ JSON)", 'yellow'))
            print(color_text(" 2. Импорт паролей (из JSON)", 'yellow'))
            print(color_text(" 0. Назад", 'white'))

            sub_choice = input(color_text("\nВыберите действие (0-2): ", 'cyan'))

            if sub_choice == "1":
                filename = export_passwords(passwords)
                print(color_text(f"\n✅ Пароли экспортированы в файл: {filename}", 'green'))
                print(color_text("⚠️ ВНИМАНИЕ! Файл НЕ ЗАШИФРОВАН! Храните его в безопасном месте.", 'red'))

            elif sub_choice == "2":
                filename = input("Имя файла для импорта (passwords_export.json): ").strip()
                if not filename:
                    filename = "passwords_export.json"

                if not os.path.exists(filename):
                    print(color_text(f"\n❌ Файл {filename} не найден!", 'red'))
                else:
                    try:
                        imported = import_passwords(filename)
                        count = 0
                        for site, data in imported.items():
                            if site not in passwords:
                                passwords[site] = data
                                count += 1
                        if count > 0:
                            encrypted = encrypt(passwords, master, salt)
                            with open(DATA_FILE, "wb") as f:
                                f.write(encrypted)
                            print(color_text(f"\n✅ Импортировано {count} новых сайтов!", 'green'))
                        else:
                            print(color_text("\n📭 Новых сайтов не найдено (все уже есть)", 'yellow'))
                    except Exception as e:
                        print(color_text(f"\n❌ Ошибка импорта: {e}", 'red'))

            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "8":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n--- СТАТИСТИКА ---\n", 'green'))

            total, weak = show_statistics(passwords)
            strong = total - weak

            print(color_text(f"📊 Всего паролей: {total}", 'cyan'))
            print(color_text(f"🔒 Сильных (8+ символов): {strong}", 'green'))
            print(color_text(f"⚠️ Слабых (менее 8 символов): {weak}", 'yellow'))

            if total > 0:
                percent = (strong / total) * 100
                print(color_text(f"\n📈 Общая надёжность: {percent:.1f}%", 'cyan'))

            print(color_text("\n--- РЕЗЕРВНОЕ КОПИРОВАНИЕ ---\n", 'green'))
            backup_choice = input("Создать резервную копию зашифрованных файлов? (д/н): ")
            if backup_choice.lower() == 'д':
                backup_dir = backup_passwords(passwords)
                print(color_text(f"\n✅ Резервная копия создана в папке: {backup_dir}", 'green'))
                print(color_text("Файлы: passwords.enc и salt.bin", 'green'))

            input(color_text("\nНажмите Enter для возврата в меню...", 'white'))

        elif choice == "9":
            clear_screen()
            print(color_text("=" * 50, 'cyan'))
            print(color_text("   МЕНЕДЖЕР ПАРОЛЕЙ С ШИФРОВАНИЕМ", 'yellow'))
            print(color_text("   (AES-256)", 'yellow'))
            print(color_text("=" * 50, 'cyan'))
            print(color_text("\n👋 До свидания! Ваши пароли сохранены.\n", 'green'))
            break

        else:
            print(color_text("\n❌ Неверный выбор! Введите число от 1 до 9.", 'red'))
            input(color_text("\nНажмите Enter для продолжения...", 'white'))


if __name__ == "__main__":
    main()
