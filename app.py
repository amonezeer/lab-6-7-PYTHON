import json
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from PIL import Image, ImageTk
import geocoder
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# Клас для роботи з API погоди
class WeatherAPI:
    def __init__(self):
        # Ініціалізація API ключа
        self.api_key = "64e22006f1b7c78ee2880271d56a1f9b"

    def get_city_coordinates(self, city: str) -> tuple:
        # Отримання координат міста
        try:
            response = requests.get(
                f"https://api.openweathermap.org/geo/1.0/direct",
                params={"q": city, "limit": 1, "appid": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
            else:
                raise ValueError("Місто не знайдено")
        except Exception as e:
            print(f"Помилка отримання координат: {e}")
            return None, None

    def get_weather(self, city: str) -> dict:
        # Отримання поточної погоди
        city_coordinates = self.get_city_coordinates(city)
        if city_coordinates:
            lat, lon = city_coordinates
        else:
            print("Місто не знайдено, спробуйте інше місто.")
            return {}

        try:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "units": "metric", "appid": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            return {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "translated_description": self.translate_description(data["weather"][0]["description"]),
            }
        except requests.RequestException as e:
            print(f"Помилка API: {e}")
            return {}

    def get_hourly_forecast(self, city: str) -> dict:
        # Отримання погодинного прогнозу
        city_coordinates = self.get_city_coordinates(city)
        if city_coordinates:
            lat, lon = city_coordinates
        else:
            print("Місто не знайдено, спробуйте інше місто.")
            return []

        try:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast/hourly",
                params={"lat": lat, "lon": lon, "cnt": 24, "units": "metric", "appid": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            forecast_list = []
            for item in data["list"]:
                forecast_list.append({
                    "datetime": datetime.fromtimestamp(item["dt"]).strftime('%H:%M'),
                    "temperature": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "description": item["weather"][0]["description"],
                    "translated_description": self.translate_description(item["weather"][0]["description"]),
                    "wind_speed": item["wind"]["speed"],
                    "humidity": item["main"]["humidity"]
                })
            return forecast_list
        except requests.RequestException as e:
            print(f"Помилка API: {e}")
            return []

    def get_weekly_forecast(self, city: str) -> dict:
        # Отримання тижневого прогнозу
        city_coordinates = self.get_city_coordinates(city)
        if city_coordinates:
            lat, lon = city_coordinates
        else:
            print("Місто не знайдено, спробуйте інше місто.")
            return []

        try:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast/daily",
                params={"lat": lat, "lon": lon, "appid": self.api_key, "cnt": 7, "units": "metric"}
            )
            response.raise_for_status()
            data = response.json()
            weekly_forecast_list = []
            for day in data["list"]:
                weekly_forecast_list.append({
                    "day": self.translate_day(datetime.fromtimestamp(day["dt"]).strftime("%A")),
                    "temperature_day": day["temp"]["max"],
                    "temperature_night": day["temp"]["min"],
                    "description": day["weather"][0]["description"],
                    "translated_description": self.translate_description(day["weather"][0]["description"]),
                })
            return weekly_forecast_list
        except requests.exceptions.RequestException as e:
            print(f"Помилка отримання даних: {e}")
            return []

    def translate_description(self, description: str) -> str:
        # Переклад опису погоди
        translations = {
            "clear sky": "Ясне небо",
            "mostly clear": "Переважно ясно",
            "few clouds": "Мало хмар",
            "scattered clouds": "Розсіяні хмари",
            "broken clouds": "Розірвані хмари",
            "overcast clouds": "Похмуро",
            "light rain": "Легкий дощ",
            "moderate rain": "Помірний дощ",
            "heavy intensity rain": "Сильний дощ",
            "very heavy rain": "Дуже сильний дощ",
            "extreme rain": "Екстремальний дощ",
            "freezing rain": "Зледенілий дощ",
            "light shower rain": "Легка злива",
            "heavy shower rain": "Сильна злива",
            "ragged shower rain": "Нерівна злива",
            "drizzle": "Мряка",
            "thunderstorm with light rain": "Гроза з легким дощем",
            "thunderstorm with heavy rain": "Гроза з сильним дощем",
            "light thunderstorm": "Легка гроза",
            "heavy thunderstorm": "Сильна гроза",
            "ragged thunderstorm": "Нерівна гроза",
            "light snow": "Легкий сніг",
            "heavy snow": "Сильний сніг",
            "sleet": "Дощ зі снігом",
            "showers snow": "Снігопад",
            "blowing snow": "Вітряний сніг",
            "blizzard": "Сніговий буран",
            "mist": "Туман",
            "fog": "Туман",
            "haze": "Мряка",
            "smoke": "Дим",
            "dust": "Пил",
            "sand": "Пісок",
            "volcanic ash": "Вулканічний попіл",
            "tornado": "Торнадо",
            "squall": "Шквал",
            "tropical storm": "Тропічний шторм",
            "hurricane": "Ураган",
            "rain and sun": "Дощ і сонце",
            "rain and clouds": "Дощ і хмари",
            "snow and sun and clouds": "Сніг, сонце і хмари",
            "snow and clouds": "Сніг і хмари",
            "mixed rain and snow": "Змішаний дощ і сніг",
            "very cold": "Дуже холодно",
            "very hot": "Дуже жарко",
            "windy": "Вітряно",
            "umbrella (general rain)": "Парасолька (загальний дощ)"
        }
        return translations.get(description.lower(), description)

    def translate_day(self, day: str) -> str:
        # Переклад назви дня тижня
        translations = {
            "Monday": "Понеділок",
            "Tuesday": "Вівторок",
            "Wednesday": "Середа",
            "Thursday": "Четвер",
            "Friday": "П’ятниця",
            "Saturday": "Субота",
            "Sunday": "Неділя"
        }
        return translations.get(day, day)

# Основний клас додатку
class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Ініціалізація API та параметрів
        self.weather_api = WeatherAPI()
        self.current_graph = None

        # Налаштування головного вікна
        self.title("Погодний додаток")
        self.geometry("1000x700")

        # Створення вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.weather_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.weather_tab, text="Погода")

        self.graphics_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.graphics_tab, text="Графіки")

        # Поле пошуку
        self.search_frame = tk.Frame(self.weather_tab, bg="white")
        self.search_frame.pack(pady=10)

        self.search_entry = tk.Entry(self.search_frame, width=30, font=("Arial", 12))
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", self.submit)

        self.search_button = tk.Button(self.search_frame, text="Пошук", command=self.submit)
        self.search_button.pack(side="left", padx=5)

        self.gps_button = tk.Button(self.search_frame, text="Локацiя", command=self.locate_city)
        self.gps_button.pack(side="left", padx=5)

        # Відображення помилок
        self.error_label = tk.Label(self.weather_tab, text="", fg="red", bg="white", font=("Arial", 12))
        self.error_label.pack(pady=5)

        # Фрейми для відображення даних
        self.city_info_frame = tk.Frame(self.weather_tab, bg="white")
        self.city_info_frame.pack(fill="x", padx=10, pady=5)

        self.hourly_frame = tk.Frame(self.weather_tab, bg="white")
        self.hourly_frame.pack(fill="x", padx=10, pady=5)

        self.weekly_frame = tk.Frame(self.weather_tab, bg="white")
        self.weekly_frame.pack(fill="x", padx=10, pady=5)

        self.graphics_frame = tk.Frame(self.graphics_tab, bg="white")
        self.graphics_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопки для графіків
        self.graph_frame = tk.Frame(self.graphics_tab, bg="white")
        self.graph_frame.pack(pady=5)
        tk.Button(self.graph_frame, text="Температура", command=lambda: self.update_graph("temperature")).pack(side="left", padx=5)
        tk.Button(self.graph_frame, text="Швидкість вітру", command=lambda: self.update_graph("wind")).pack(side="left", padx=5)

    def locate_city(self):
        # Визначення міста за GPS
        city = geocoder.ip("me").city
        if city:
            self.submit(city=city)
        else:
            self.error_label.config(text="Не вдалося визначити місто за GPS")

    def submit(self, event=None, city=None):
        # Обробка введення міста
        manual_input = False
        if city is None:
            city = self.search_entry.get().strip()
            manual_input = True

        if not city:
            self.error_label.config(text="Будь ласка, введіть місто")
            return
        elif not city.replace(" ", "").replace("-", "").isalpha():
            self.error_label.config(text="Введіть коректну назву міста")
            return

        if manual_input:
            self.search_entry.delete(0, tk.END)

        # Оновлення даних
        weather = self.weather_api.get_weather(city)
        forecast = self.weather_api.get_hourly_forecast(city)
        weekly_forecast = self.weather_api.get_weekly_forecast(city)

        if weather and forecast and weekly_forecast:
            self.error_label.config(text="")
            self.update_current_weather(weather)
            self.update_current_forecast(forecast)
            self.update_current_weekly_forecast(weekly_forecast)
            self.update_graph("temperature")
        else:
            self.error_label.config(text="Не вдалося отримати дані про погоду")

    def update_current_weather(self, weather):
        # Оновлення поточної погоди
        for widget in self.city_info_frame.winfo_children():
            widget.destroy()

        tk.Label(self.city_info_frame, text=f"Місто: {weather['city']}", font=("Arial", 16), bg="white").pack(anchor="w")
        tk.Label(self.city_info_frame, text=f"Опис: {weather['translated_description']}", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(self.city_info_frame, text=f"Температура: {round(weather['temperature'])}°C", font=("Arial", 14), bg="white").pack(anchor="w")
        tk.Label(self.city_info_frame, text=f"Відчувається як: {round(weather['feels_like'])}°C", font=("Arial", 12), bg="white").pack(anchor="w")

    def update_current_forecast(self, forecast):
        # Оновлення погодинного прогнозу
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        for i, item in enumerate(forecast):
            frame = tk.Frame(self.hourly_frame, bg="lightgray", bd=1, relief="solid", width=80, height=80)
            frame.pack(side="left", padx=2, pady=2)

            tk.Label(frame, text=f"Час: {item['datetime']}", font=("Arial", 8), bg="lightgray", wraplength=80).pack()
            tk.Label(frame, text=f"Темп.: {round(item['temperature'])}°C", font=("Arial", 10), bg="lightgray").pack()

            # Додавання іконки
            day_time = "day" if 6 <= int(item["datetime"][:-3]) < 20 else "night"
            icon_name = self.get_icon_name(item["description"], day_time)
            try:
                img_path = os.path.join("resources", "weather", f"{icon_name}.png")
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Файл {icon_name}.png не знайдено в {img_path}")
                img = Image.open(img_path).resize((40, 40), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(frame, image=photo, bg="lightgray")
                icon_label.image = photo
                icon_label.pack()
            except FileNotFoundError as e:
                print(f"Помилка: {e}")
                tk.Label(frame, text=f"[Відсутній: {icon_name}]", fg="red", font=("Arial", 8), bg="lightgray").pack()
            except Exception as e:
                print(f"Помилка завантаження іконки {icon_name}: {e}")
                tk.Label(frame, text="[Помилка]", fg="red", font=("Arial", 8), bg="lightgray").pack()

    def update_current_weekly_forecast(self, weekly_forecast):
        # Оновлення тижневого прогнозу
        for widget in self.weekly_frame.winfo_children():
            widget.destroy()

        for i, item in enumerate(weekly_forecast):
            frame = tk.Frame(self.weekly_frame, bg="lightgray", bd=1, relief="solid")
            frame.pack(fill="x", padx=5, pady=2)

            desc = "ясне небо" if item["translated_description"] == "Ясне небо" else item["translated_description"]
            day_label = "Сьогодні" if i == 0 else "Завтра" if i == 1 else item["day"]
            tk.Label(frame, text=f"{day_label}: {desc}", font=("Arial", 12), bg="lightgray").pack(side="left", padx=5)
            tk.Label(frame, text=f"День: {round(item['temperature_day'])}°C", font=("Arial", 12), bg="lightgray").pack(side="left", padx=5)
            tk.Label(frame, text=f"Ніч: {round(item['temperature_night'])}°C", font=("Arial", 12), bg="lightgray").pack(side="left", padx=5)

            # Додавання іконки
            day_time = "day"
            icon_name = self.get_icon_name(item["description"], day_time)
            try:
                img_path = os.path.join("resources", "weather", f"{icon_name}.png")
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Файл {icon_name}.png не знайдено в {img_path}")
                img = Image.open(img_path).resize((40, 40), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(frame, image=photo, bg="lightgray")
                icon_label.image = photo
                icon_label.pack(side="left", padx=5)
            except FileNotFoundError as e:
                print(f"Помилка: {e}")
                tk.Label(frame, text=f"[Відсутній: {icon_name}]", fg="red", font=("Arial", 8), bg="lightgray").pack(side="left", padx=5)
            except Exception as e:
                print(f"Помилка завантаження іконки {icon_name}: {e}")
                tk.Label(frame, text="[Помилка]", fg="red", font=("Arial", 8), bg="lightgray").pack(side="left", padx=5)

    def get_icon_name(self, description: str, day_time: str = "day") -> str:
        # Отримання назви іконки
        try:
            with open("weather_icons_mapping.json", "r", encoding="utf-8") as f:
                icons_data = json.load(f)
        except FileNotFoundError:
            print("JSON файл не знайдено")
            return "default"
        except json.JSONDecodeError:
            print("Помилка при читанні weather_icons_mapping.json")
            return "default"

        weather_mapping = icons_data.get("weather_icons_mapping", {})
        description_lower = description.lower()

        for category in weather_mapping.values():
            for desc_pattern, icon_info in category.items():
                if desc_pattern.lower() in description_lower or description_lower in desc_pattern.lower():
                    if isinstance(icon_info, dict):
                        return icon_info.get(day_time, "default")
                    elif isinstance(icon_info, str):
                        return icon_info
        return "default"

    def update_graph(self, graph_type):
        # Оновлення графіків
        if self.current_graph:
            self.current_graph.get_tk_widget().pack_forget()
        forecast = self.weather_api.get_hourly_forecast(self.search_entry.get().strip() or "Odessa")

        hours = [item["datetime"] for item in forecast]
        if graph_type == "temperature":
            # Графік температури
            temperatures = [item["temperature"] for item in forecast]
            feels_like = [item["feels_like"] for item in forecast]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(hours, temperatures, label="Температура", color="orange", marker="o")
            ax.plot(hours, feels_like, label="Відчувається", color="blue", linestyle="--", marker="x")
            ax.set_xlabel("Година")
            ax.set_ylabel("Температура (°C)")
            ax.legend()
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True)
        elif graph_type == "wind":
            # Графік швидкості вітру
            wind_speeds = [item["wind_speed"] for item in forecast]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(hours, wind_speeds, label="Швидкість вітру", color="green")
            ax.set_xlabel("Година")
            ax.set_ylabel("Швидкість вітру (м/с)")
            ax.legend()
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, axis="y")


        self.current_graph = FigureCanvasTkAgg(fig, master=self.graphics_frame)
        self.current_graph.draw()
        self.current_graph.get_tk_widget().pack(pady=5)

if __name__ == "__main__":
    # Запуск додатку
    app = WeatherApp()
    app.mainloop()