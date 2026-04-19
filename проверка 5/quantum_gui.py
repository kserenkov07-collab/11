"""
Модуль графического интерфейса в стиле QuantumVault Explorer.
Сохраняет функциональность wallet_checker с новым интерфейсом.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
from datetime import datetime
from wallet_checker import WalletChecker
from config import Config
from optimized_executor import optimized_executor
from logger import logger, setup_logger

class RoundedButton(tk.Canvas):
    """Кастомная кнопка со скругленными углами"""
    def __init__(self, master=None, text="", radius=25, color="#555", text_color="white", 
                 hover_color="#444", click_color="#333", command=None, width=100, height=40, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, **kwargs)
        self.radius = radius
        self.original_color = color
        self.color = color
        self.text_color = text_color
        self.hover_color = hover_color
        self.click_color = click_color
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.is_clicked = False
        
        # Устанавливаем фон холста в цвет кнопки, чтобы скругленные углы были того же цвета
        self.configure(bg=color)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        self.draw_button()
        
    def draw_button(self):
        """Отрисовка кнопки со скругленными углами"""
        self.delete("all")
        
        # Устанавливаем фон холста в цвет кнопки
        self.configure(bg=self.color)
        
        # Рисуем скругленный прямоугольник
        self.create_arc((0, 0, self.radius*2, self.radius*2), start=90, extent=90, 
                       fill=self.color, outline=self.color)
        self.create_arc((self.width-self.radius*2, 0, self.width, self.radius*2), start=0, 
                       extent=90, fill=self.color, outline=self.color)
        self.create_arc((self.width-self.radius*2, self.height-self.radius*2, self.width, 
                       self.height), start=270, extent=90, fill=self.color, outline=self.color)
        self.create_arc((0, self.height-self.radius*2, self.radius*2, self.height), start=180, 
                       extent=90, fill=self.color, outline=self.color)
        
        # Рисуем прямоугольники для заполнения
        self.create_rectangle(self.radius, 0, self.width-self.radius, self.height, 
                            fill=self.color, outline=self.color)
        self.create_rectangle(0, self.radius, self.width, self.height-self.radius, 
                            fill=self.color, outline=self.color)
        
        # Добавляем текст
        self.create_text(self.width/2, self.height/2, text=self.text, fill=self.text_color, 
                       font=("Arial", 10, "bold"))
    
    def on_enter(self, event):
        """Обработчик наведения мыши"""
        if not self.is_clicked:
            self.color = self.hover_color
            self.configure(bg=self.color)
            self.draw_button()
    
    def on_leave(self, event):
        """Обработчик ухода мыши"""
        if not self.is_clicked:
            self.color = self.original_color
            self.configure(bg=self.color)
            self.draw_button()
    
    def on_click(self, event):
        """Обработчик клика"""
        self.is_clicked = True
        self.color = self.click_color
        self.configure(bg=self.color)
        self.draw_button()
    
    def on_release(self, event):
        """Обработчик отпускания кнопки"""
        self.is_clicked = False
        self.color = self.hover_color
        self.configure(bg=self.color)
        self.draw_button()
        
        if self.command:
            self.command()
    
    def reset(self):
        """Сброс состояния кнопки"""
        self.is_clicked = False
        self.color = self.original_color
        self.configure(bg=self.color)
        self.draw_button()

class LogWindow(tk.Toplevel):
    """Окно для просмотра логов"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Журнал событий")
        self.geometry("800x400")
        self.configure(bg='#2b2b2b')
        
        # Создаем текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(
            self, 
            wrap=tk.WORD, 
            bg='#1e1e1e', 
            fg='#00ff00',
            font=("Consolas", 9),
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопка очистки логов
        clear_btn = RoundedButton(
            self, 
            text="Очистить", 
            radius=15, 
            width=100, 
            height=30,
            color="#555", 
            hover_color="#444", 
            click_color="#333",
            command=self.clear_logs
        )
        clear_btn.pack(pady=5)
        
    def clear_logs(self):
        """Очистка логов"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
    
    def append_log(self, message):
        """Добавление сообщения в лог"""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

class QuantumWalletGUI:
    """Класс графического интерфейса в стиле QuantumVault Explorer"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Wallet Scanner")
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')
        self.root.resizable(True, True)
        
        # Создаем окно для логов
        self.log_window = None
        
        # Сначала загружаем словари
        self.wordlists = self.load_bip39_wordlists()
        if not self.wordlists:
            messagebox.showerror("Ошибка", "Не удалось загрузить словари BIP-39")
            return
        
        # Затем загружаем известные кошельки
        self.load_known_wallets()
        
        # И только потом настраиваем GUI
        self.checker = None
        self.check_thread = None
        
        # Статистика
        self.checked_count = 0
        self.found_count = 0
        self.start_time = None
        self.is_running = False
        self.settings_window = None
        self.update_interval = None
        self.last_update_time = None
        self.last_checked_count = 0
        self.active_threads = 0
        
        # Перенастраиваем логгер для использования GUI callback
        setup_logger(self.log_callback)
        
        self.setup_gui()
    
    def log_callback(self, message):
        """Callback-функция для получения логов"""
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.append_log(message)
    
    def show_logs(self):
        """Показать окно с логами"""
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = LogWindow(self.root)
        else:
            self.log_window.lift()
    
    def load_bip39_wordlists(self):
        """Быстрая загрузка словарей BIP-39"""
        wordlists = {}
        languages = {
            "english": "english.txt",
            "french": "french.txt", 
            "spanish": "spanish.txt",
            "italian": "italian.txt",
            "portuguese": "portuguese.txt",
            "czech": "czech.txt"
        }
        
        for lang, filename in languages.items():
            file_path = f"{Config.WORDLISTS_DIR}/{filename}"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    wordlists[lang] = [line.strip() for line in f.readlines()]
                print(f"✅ Загружен словарь: {lang} ({len(wordlists[lang])} слов)")
            except:
                print(f"❌ Ошибка загрузки словаря: {lang}")
        
        return wordlists
    
    def load_known_wallets(self):
        """Загрузка известных кошельков из файлов"""
        from known_wallets import known_wallets_db
        
        # Импорт из файлов
        import_files = [
            "known_eth_wallets.txt",
            "known_btc_wallets.txt",
            "active_wallets.txt"
        ]
        
        imported = 0
        for file in import_files:
            if os.path.exists(file):
                imported += known_wallets_db.import_from_file(file)
        
        if imported > 0:
            print(f"✅ Загружено {imported} известных кошельков")
    
    def setup_gui(self):
        """Настройка элементов интерфейса в стиле QuantumVault"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#2b2b2b')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_label = tk.Label(header_frame, text="Wallet Scanner", 
                              font=("Arial", 20, "bold"), fg="#00ff00", bg='#2b2b2b')
        title_label.pack(side=tk.LEFT, expand=True)
        
        # Settings button
        self.settings_btn = RoundedButton(header_frame, text="⚙️", radius=15, width=40, height=40,
                                         color="#555", hover_color="#444", click_color="#333",
                                         command=self.show_settings)
        self.settings_btn.pack(side=tk.RIGHT, padx=5)
        
        # Logs button
        self.logs_btn = RoundedButton(header_frame, text="📋", radius=15, width=40, height=40,
                                     color="#555", hover_color="#444", click_color="#333",
                                     command=self.show_logs)
        self.logs_btn.pack(side=tk.RIGHT, padx=5)
        
        # Stats frame
        stats_frame = tk.LabelFrame(main_frame, text="📊 Статистика в реальном времени", 
                                   font=("Arial", 10, "bold"), fg="#00ff00", bg='#2b2b2b',
                                   relief=tk.FLAT, bd=1)
        stats_frame.pack(fill=tk.X, pady=5)
        
        # Grid for stats
        stats_grid = tk.Frame(stats_frame, bg='#2b2b2b')
        stats_grid.pack(fill=tk.X, pady=5)
        
        self.stats_labels = {}
        stats_data = [
            ("Проверено кошельков:", "total_checked", "0"),
            ("Кошельков с балансом:", "found_count", "0"),
            ("Скорость (кош/сек):", "speed", "0"),
            ("Активных потоков:", "active_threads", "0")
        ]
        
        for i, (text, key, value) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            
            frame = tk.Frame(stats_grid, bg='#2b2b2b')
            frame.grid(row=row, column=col, sticky="w", padx=10, pady=5)
            
            lbl = tk.Label(frame, text=text, font=("Arial", 9), fg="white", bg='#2b2b2b')
            lbl.pack(side=tk.LEFT)
            
            value_lbl = tk.Label(frame, text=value, font=("Arial", 9, "bold"), 
                               fg="#00ff00", bg='#2b2b2b')
            value_lbl.pack(side=tk.LEFT)
            
            self.stats_labels[key] = value_lbl
        
        # Session time (separate row)
        time_frame = tk.Frame(stats_frame, bg='#2b2b2b')
        time_frame.pack(fill=tk.X, pady=5)
        
        lbl = tk.Label(time_frame, text="Время сессии:", font=("Arial", 9), fg="white", bg='#2b2b2b')
        lbl.pack(side=tk.LEFT, padx=10)
        
        self.stats_labels['session_time'] = tk.Label(time_frame, text="00:00:00", 
                                                   font=("Arial", 9, "bold"), fg="#00ff00", 
                                                   bg='#2b2b2b')
        self.stats_labels['session_time'].pack(side=tk.LEFT)
        
        # Activity log
        log_frame = tk.LabelFrame(main_frame, text="📝 Журнал активности", 
                                 font=("Arial", 10, "bold"), fg="#00ff00", bg='#2b2b2b',
                                 relief=tk.FLAT, bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Создаем кастомный скроллбар с темным фоном
        self.log_text = tk.Text(log_frame, height=15, font=("Consolas", 8), 
                               bg='#1e1e1e', fg='#00ff00', wrap=tk.WORD,
                               insertbackground='white', relief=tk.FLAT, bd=0)
        
        # Создаем скроллбар и настраиваем его цвета
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview,
                                bg='#1a1a1a', troughcolor='#2b2b2b', activebackground='#333333')
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Упаковываем элементы
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        # Control buttons
        btn_frame = tk.Frame(main_frame, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = RoundedButton(btn_frame, text="Старт", radius=15, width=100, height=40,
                                      color="#2e7d32", hover_color="#1b5e20", click_color="#0d4712",
                                      command=self.start_checking)
        self.start_btn.pack(side=tk.LEFT, padx=20)
        
        self.stop_btn = RoundedButton(btn_frame, text="Стоп", radius=15, width=100, height=40,
                                     color="#c62828", hover_color="#b71c1c", click_color="#8e0e0e",
                                     command=self.stop_checking)
        self.stop_btn.pack(side=tk.RIGHT, padx=20)
        
        # Center the buttons
        tk.Frame(btn_frame, bg='#2b2b2b', width=100).pack(side=tk.LEFT, expand=True)
        tk.Frame(btn_frame, bg='#2b2b2b', width=100).pack(side=tk.RIGHT, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def show_settings(self):
        """Показать настройки"""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
            
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Настройки")
        self.settings_window.geometry("500x650")
        self.settings_window.configure(bg='#2b2b2b')
        self.settings_window.resizable(False, False)
        
        # Main frame
        main_frame = tk.Frame(self.settings_window, bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Настройки", 
                             font=("Arial", 16, "bold"), fg="#00ff00", bg='#2b2b2b')
        title_label.pack(pady=(0, 15))
        
        # Scrollable frame for settings
        canvas_frame = tk.Frame(main_frame, bg='#2b2b2b')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview,
                                bg='#1a1a1a', troughcolor='#2b2b2b', activebackground='#333333')
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Создаем переменные для хранения значений
        settings_vars = {}
        
        # Параметры для отображения
        settings = [
            ("MIN_TOTAL_BALANCE_USD", "Минимальный общий баланс (USD):", "float"),
            ("MIN_TX_COUNT", "Мин. количество транзакций:", "int"),
            ("MIN_INACTIVE_DAYS", "Мин. дней бездействия:", "int"),
            ("MAX_WORKERS", "Максимальное количество потоков:", "int"),
            ("BATCH_SIZE", "Размер пакета:", "int"),
            ("REQUEST_TIMEOUT", "Таймаут запроса (сек):", "int"),
            ("CACHE_EXPIRY", "Время жизни кэша (сек):", "int"),
            ("USE_HUMAN_PATTERNS", "Использовать человеческие паттерны:", "bool"),
            ("USE_TX_ACTIVITY_CHECK", "Проверка активности кошелька:", "bool"),
            ("USE_MULTIPLE_API_SOURCES", "Использовать несколько API:", "bool"),
            ("USE_BATCH_API", "Использовать пакетные API запросы:", "bool"),
            ("USE_PREFILTERING", "Использовать предварительную фильтрацию:", "bool"),
            ("PREFILTER_THRESHOLD", "Порог предварительной фильтрации:", "int")
        ]
        
        for i, (setting_key, label_text, var_type) in enumerate(settings):
            frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
            frame.pack(fill=tk.X, pady=5)
            
            lbl = tk.Label(frame, text=label_text, font=("Arial", 9), fg="white", bg='#2b2b2b')
            lbl.pack(side=tk.LEFT, padx=5)
            
            if var_type == "bool":
                var = tk.BooleanVar(value=getattr(Config, setting_key))
                chk = tk.Checkbutton(frame, variable=var, bg='#2b2b2b', fg="white", 
                                   selectcolor="#00ff00")
                chk.pack(side=tk.RIGHT, padx=5)
            else:
                var = tk.StringVar(value=str(getattr(Config, setting_key)))
                entry = tk.Entry(frame, textvariable=var, width=15, bg='#1e1e1e', fg="white",
                               insertbackground="white")
                entry.pack(side=tk.RIGHT, padx=5)
            
            settings_vars[setting_key] = (var, var_type)
        
        # Добавляем настройки длины мнемонической фразы
        frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        frame.pack(fill=tk.X, pady=5)
        
        lbl = tk.Label(frame, text="Длина мнемонической фразы:", font=("Arial", 9), 
                     fg="white", bg='#2b2b2b')
        lbl.pack(side=tk.LEFT, padx=5)
        
        mnemonic_length_var = tk.StringVar(value=str(Config.MNEMONIC_LENGTH))
        mnemonic_length_combo = ttk.Combobox(frame, textvariable=mnemonic_length_var, 
                                           values=["12", "15", "18", "21", "24"], width=12,
                                           state="readonly")
        mnemonic_length_combo.pack(side=tk.RIGHT, padx=5)
        settings_vars['MNEMONIC_LENGTH'] = (mnemonic_length_var, "int")
        
        # Добавляем настройки выбора языков
        frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        frame.pack(fill=tk.X, pady=5)
        
        lbl = tk.Label(frame, text="Выбор языков:", font=("Arial", 9), 
                     fg="white", bg='#2b2b2b')
        lbl.pack(side=tk.LEFT, padx=5)
        
        # Фрейм для чекбоксов языков (вертикальное расположение)
        lang_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        lang_frame.pack(fill=tk.X, pady=5)
        
        lang_vars = {}
        for lang in self.wordlists.keys():
            var = tk.BooleanVar(value=lang in Config.ENABLED_LANGUAGES)
            chk = tk.Checkbutton(lang_frame, text=lang, variable=var, bg='#2b2b2b', 
                               fg="white", selectcolor="#00ff00", anchor="w")
            chk.pack(fill=tk.X, padx=20, pady=2)
            lang_vars[lang] = var
        
        settings_vars['ENABLED_LANGUAGES'] = (lang_vars, "lang_list")
        
        # Добавляем настройки выбора валют
        frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        frame.pack(fill=tk.X, pady=5)
        
        lbl = tk.Label(frame, text="Выбор валют для проверки:", font=("Arial", 9), 
                     fg="white", bg='#2b2b2b')
        lbl.pack(side=tk.LEFT, padx=5)
        
        # Фрейм для чекбоксов валют (вертикальное расположение)
        currency_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        currency_frame.pack(fill=tk.X, pady=5)
        
        currency_vars = {}
        for currency in Config.CRYPTOCURRENCIES.keys():
            var = tk.BooleanVar(value=currency in Config.TARGET_CURRENCIES)
            chk = tk.Checkbutton(currency_frame, text=currency, variable=var, bg='#2b2b2b', 
                               fg="white", selectcolor="#00ff00", anchor="w")
            chk.pack(fill=tk.X, padx=20, pady=2)
            currency_vars[currency] = var
        
        settings_vars['TARGET_CURRENCIES'] = (currency_vars, "currency_list")
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def save_settings():
            try:
                for setting_key, (var, var_type) in settings_vars.items():
                    if setting_key == 'ENABLED_LANGUAGES':
                        # Обработка списка языков
                        enabled_langs = [lang for lang, var in var.items() if var.get()]
                        if enabled_langs:  # Проверяем, что выбран хотя бы один язык
                            setattr(Config, setting_key, enabled_langs)
                        else:
                            messagebox.showerror("Ошибка", "Необходимо выбрать хотя бы один язык")
                            return
                    elif setting_key == 'TARGET_CURRENCIES':
                        # Обработка списка валют
                        enabled_currencies = [currency for currency, var in var.items() if var.get()]
                        if enabled_currencies:  # Проверяем, что выбрана хотя бы одна валюта
                            setattr(Config, setting_key, enabled_currencies)
                        else:
                            messagebox.showerror("Ошибка", "Необходимо выбрать хотя бы одну валюту")
                            return
                    else:
                        value = var.get()
                        
                        if var_type == "int":
                            setattr(Config, setting_key, int(value))
                        elif var_type == "float":
                            setattr(Config, setting_key, float(value))
                        elif var_type == "bool":
                            setattr(Config, setting_key, bool(value))
                        else:
                            setattr(Config, setting_key, value)
                
                # Сохраняем настройки
                Config.save_settings()
                
                self.log_message("✅ Настройки сохранены")
                self.settings_window.destroy()
                self.settings_window = None
                
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректное значение: {e}")
        
        def cancel_settings():
            self.settings_window.destroy()
            self.settings_window = None
        
        # Кнопки сохранения и отмены (внизу под всеми настройками)
        btn_frame = tk.Frame(main_frame, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, pady=20)
        
        self.save_btn = RoundedButton(btn_frame, text="Сохранить", radius=15, width=100, height=40,
                                     color="#2e7d32", hover_color="#1b5e20", click_color="#0d4712",
                                     command=save_settings)
        self.save_btn.pack(side=tk.LEFT, padx=20)
        
        self.cancel_btn = RoundedButton(btn_frame, text="Отмена", radius=15, width=100, height=40,
                                       color="#c62828", hover_color="#b71c1c", click_color="#8e0e0e",
                                       command=cancel_settings)
        self.cancel_btn.pack(side=tk.RIGHT, padx=20)
        
        # Center the buttons
        tk.Frame(btn_frame, bg='#2b2b2b', width=100).pack(side=tk.LEFT, expand=True)
        tk.Frame(btn_frame, bg='#2b2b2b', width=100).pack(side=tk.RIGHT, expand=True)
        
        # Обработка закрытия окна
        self.settings_window.protocol("WM_DELETE_WINDOW", cancel_settings)
    
    def log_message(self, message):
        """Добавление сообщения в журнал"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def format_time(self, seconds):
        """Форматирование времени"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def update_stats(self):
        """Обновление статистики"""
        if not self.is_running:
            return
            
        current_time = time.time()
        session_elapsed = current_time - self.start_time
        
        # Получаем количество активных потоков из исполнителя
        if optimized_executor.executor:
            try:
                # Получаем количество активных потоков
                self.active_threads = optimized_executor.executor._max_workers - optimized_executor.executor._work_queue.qsize()
            except:
                # Если не удалось получить информацию, используем общее количество потоков
                self.active_threads = Config.MAX_WORKERS
        
        # Обновляем интерфейс
        self.stats_labels['total_checked'].config(text=f"{self.checked_count:,}")
        self.stats_labels['found_count'].config(text=f"{self.found_count}")
        self.stats_labels['session_time'].config(text=self.format_time(session_elapsed))
        self.stats_labels['active_threads'].config(text=f"{self.active_threads}")
        
        # Рассчитываем скорость
        speed = 0
        if self.last_update_time:
            time_diff = current_time - self.last_update_time
            count_diff = self.checked_count - self.last_checked_count
            if time_diff > 0:
                speed = count_diff / time_diff
        
        self.stats_labels['speed'].config(text=f"{speed:,.1f}")
        self.last_update_time = current_time
        self.last_checked_count = self.checked_count
        
        # Планируем следующее обновление
        if self.is_running:
            self.update_interval = self.root.after(1000, self.update_stats)
    
    def checker_callback(self, data):
        """Callback-функция для обновления GUI из WalletChecker"""
        if data['type'] == 'stats':
            self.checked_count = data['checked']
            self.found_count = data['found']
            
        elif data['type'] == 'found':
            self.found_count += 1
            result = data['result']
            self.log_message(f"💰 НАЙДЕН КОШЕЛЕК! Язык: {result['language']}")
            self.log_message(f"💰 Общий баланс: ${result['total_balance_usd']:.2f} USD")
            
            # Показываем всплывающее уведомление
            message = f"Найден кошелек с балансом!\n\n"
            message += f"Язык: {result['language']}\n"
            message += f"ETH адрес: {result['eth_address']}\n"
            message += f"BTC адрес: {result['btc_address']}\n"
            message += f"Общий баланс: ${result['total_balance_usd']:.2f} USD\n\n"
            
            message += "БАЛАНСЫ В USD:\n"
            for currency, balance in result['usd_balances'].items():
                if balance > 0:
                    message += f"{currency}: ${balance:.2f}\n"
            
            message += f"\nРезультаты сохранены в: {data['filename']}"
            
            # Используем after для показа сообщения в главном потоке
            self.root.after(0, lambda: messagebox.showinfo("Найден кошелек", message))
        
        elif data['type'] == 'finished':
            self.is_running = False
            self.log_message(f"Проверка завершена. Проверено: {data['checked']}, Найдено: {data['found']}")
            self.start_btn.reset()
            self.stop_btn.reset()
            
            # Отменяем запланированное обновление
            if self.update_interval:
                self.root.after_cancel(self.update_interval)
    
    def start_checking(self):
        """Запуск проверки"""
        if self.is_running:
            return
            
        self.is_running = True
        self.start_time = time.time()
        self.checked_count = 0
        self.found_count = 0
        
        self.log_message("🚀 ЗАПУСК СКАНИРОВАНИЯ КОШЕЛЬКОВ...")
        self.log_message(f"🌐 Загружено {len(self.wordlists)} словарей")
        self.log_message(f"📊 Целевые валюты: {', '.join(Config.TARGET_CURRENCIES)}")
        self.log_message(f"🔍 Режим: {'Человеческие паттерны' if Config.USE_HUMAN_PATTERNS else 'Случайная генерация'}")
        self.log_message(f"💰 Минимальный баланс: ${Config.MIN_TOTAL_BALANCE_USD:.2f} USD")
        self.log_message(f"📏 Длина мнемоники: {Config.MNEMONIC_LENGTH} слов")
        self.log_message(f"🌍 Языки: {', '.join(Config.ENABLED_LANGUAGES)}")
        self.log_message(f"⚡ Пакетная обработка: {'Включена' if Config.USE_BATCH_API else 'Выключена'}")
        self.log_message(f"🔎 Предварительная фильтрация: {'Включена' if Config.USE_PREFILTERING else 'Выключена'}")
        
        # Создаем и запускаем проверщик
        self.checker = WalletChecker(self.wordlists, self.checker_callback)
        
        # Запускаем в отдельном потоке
        self.check_thread = threading.Thread(target=self.checker.run_continuous_optimized)
        self.check_thread.daemon = True
        self.check_thread.start()
        
        # Запускаем обновление статистики
        self.update_stats()
    
    def stop_checking(self):
        """Остановка проверки"""
        if not self.is_running:
            return
            
        self.log_message("🛑 ОСТАНОВКА СКАНИРОВАНИЯ...")
        if self.checker:
            self.checker.stop()
        self.is_running = False
        self.start_btn.reset()
        self.stop_btn.reset()
        
        # Отменяем запланированное обновление
        if self.update_interval:
            self.root.after_cancel(self.update_interval)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuantumWalletGUI(root)
    root.mainloop()
