# -*- coding: utf-8 -*-
import json
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import geocoder
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from collections import defaultdict
import numpy as np

class WeatherAPI:
    def __init__(self):
        # Ініціалізую API ключ для доступу до OpenWeatherMap
        self.api_key = "64e22006f1b7c78ee2880271d56a1f9b"

    # Отримую координати міста через API OpenWeatherMap
    def get_city_coordinates(self, city: str) -> tuple:
        try:
            response = requests.get(
                f"https://api.openweathermap.org/geo/1.0/direct",
                params={"q": city, "limit": 1, "appid": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]["lat"], data[0]["lon"], data[0].get("country", "Unknown")
            else:
                raise ValueError("Місто не знайдено")
        except Exception as e:
            print(f"Помилка отримання координат: {e}")
            return None, None, None

    # Отримую поточну погоду для міста за координатами
    def get_weather(self, city: str) -> dict:
        lat, lon, country = self.get_city_coordinates(city)
        if lat is None:
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
                "country": country,
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "translated_description": self.translate_description(data["weather"][0]["description"]),
            }
        except requests.RequestException as e:
            print(f"Помилка API: {e}")
            return {}

    # Отримую погодинний прогноз на 5 днів для міста
    def get_hourly_forecast(self, city: str) -> list:
        lat, lon, _ = self.get_city_coordinates(city)
        if lat is None:
            print("Місто не знайдено, спробуйте інше місто.")
            return []
        try:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast",
                params={"lat": lat, "lon": lon, "cnt": 40, "units": "metric", "appid": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            forecast_list = []
            for item in data["list"]:
                forecast_list.append({
                    "datetime": datetime.fromtimestamp(item["dt"]),
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

    # Отримую тижневий прогноз, агрегуємо дані з погодинного
    def get_weekly_forecast(self, city: str) -> list:
        lat, lon, country = self.get_city_coordinates(city)
        if lat is None:
            print("Місто не знайдено, спробуйте інше місто.")
            return []
        try:
            hourly_forecast = self.get_hourly_forecast(city)
            if not hourly_forecast:
                return []
            daily_humidity = defaultdict(list)
            daily_data = defaultdict(dict)
            for item in hourly_forecast:
                day = item["datetime"].strftime("%Y-%m-%d")
                daily_humidity[day].append(item["humidity"])
                daily_data[day]["datetime"] = item["datetime"]
                daily_data[day]["description"] = item["description"]
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast/daily",
                params={"lat": lat, "lon": lon, "appid": self.api_key, "cnt": 7, "units": "metric"}
            )
            response.raise_for_status()
            data = response.json()
            weekly_forecast_list = []
            for i, day in enumerate(data["list"]):
                day_str = datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d")
                avg_humidity = np.mean(daily_humidity[day_str]) if day_str in daily_humidity else 0
                weekly_forecast_list.append({
                    "day": self.translate_day(datetime.fromtimestamp(day["dt"]).strftime("%A")),
                    "date": day_str,
                    "temperature_day": day["temp"]["max"],
                    "temperature_night": day["temp"]["min"],
                    "description": day["weather"][0]["description"],
                    "translated_description": self.translate_description(day["weather"][0]["description"]),
                    "humidity": avg_humidity,
                    "country": country
                })
            return weekly_forecast_list
        except requests.exceptions.RequestException as e:
            print(f"Помилка отримання даних: {e}")
            return []

    # Перекладаю опис погоди на українську мову
    def translate_description(self, description: str) -> str:
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

    # Перекладаю назви днів тижня на українську
    def translate_day(self, day: str) -> str:
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

class WeatherApp(tk.Tk):
    def __init__(self):
        # Ініціалізую головне вікно програми та створюю вкладки
        super().__init__()
        self.weather_api = WeatherAPI()
        self.current_graph = None
        self.current_city = None

        self.title("Погодний додаток")
        self.geometry("1300x800")
        self.configure(bg="#F5F6F5")

        self.style = ttk.Style()
        self.style.configure("TNotebook", background="#F5F6F5")
        self.style.configure("TFrame", background="#F5F6F5")
        self.style.configure("TButton", font=("Arial", 10), padding=5)
        self.style.configure("TEntry", font=("Arial", 12), padding=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.weather_tab = tk.Frame(self.notebook, bg="#F5F6F5")
        self.notebook.add(self.weather_tab, text="Погода")

        self.graphics_tab = tk.Frame(self.notebook, bg="#F5F6F5")
        self.notebook.add(self.graphics_tab, text="Графіки")

        self.search_frame = tk.Frame(self.weather_tab, bg="#F5F6F5", bd=2, relief="groove")
        self.search_frame.pack(pady=10, padx=10, fill="x")

        self.search_entry = ttk.Entry(self.search_frame, width=30, font=("Arial", 12))
        self.search_entry.pack(side="left", padx=10, pady=5)
        self.search_entry.bind("<Return>", self.submit)

        self.search_button = ttk.Button(self.search_frame, text="Пошук", command=self.submit)
        self.search_button.pack(side="left", padx=5)

        self.gps_button = ttk.Button(self.search_frame, text="Локація", command=self.locate_city)
        self.gps_button.pack(side="left", padx=5)

        self.error_label = tk.Label(self.weather_tab, text="", fg="#D32F2F", bg="#F5F6F5", font=("Arial", 12))
        self.error_label.pack(pady=5)

        self.city_info_frame = tk.Frame(self.weather_tab, bg="#FFFFFF", bd=2, relief="groove")
        self.city_info_frame.pack(fill="x", padx=10, pady=5)

        self.hourly_frame = tk.Frame(self.weather_tab, bg="#FFFFFF", bd=2, relief="groove")
        self.hourly_frame.pack(fill="x", padx=10, pady=5)

        self.weekly_frame = tk.Frame(self.weather_tab, bg="#FFFFFF", bd=2, relief="groove")
        self.weekly_frame.pack(fill="x", padx=10, pady=5)

        self.graphics_frame = tk.Frame(self.graphics_tab, bg="#FFFFFF", bd=2, relief="groove")
        self.graphics_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.graph_frame = tk.Frame(self.graphics_tab, bg="#F5F6F5")
        self.graph_frame.pack(pady=5)
        ttk.Button(self.graph_frame, text="Температура", command=lambda: self.update_graph("temperature")).pack(side="left", padx=5)
        ttk.Button(self.graph_frame, text="Швидкість вітру", command=lambda: self.update_graph("wind")).pack(side="left", padx=5)
        ttk.Button(self.graph_frame, text="Вологість", command=lambda: self.update_graph("humidity")).pack(side="left", padx=5)

    # Визначаю поточне місто за геолокацією
    def locate_city(self):
        city = geocoder.ip("me").city
        if city:
            self.submit(city=city)
        else:
            self.error_label.config(text="Не вдалося визначити місто за GPS")

    # Обробляю введення міста та запускаю оновлення даних
    def submit(self, event=None, city=None):
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
        self.current_city = city
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

    # Оновлюю відображення поточної погоди
    def update_current_weather(self, weather):
        for widget in self.city_info_frame.winfo_children():
            widget.destroy()
        tk.Label(self.city_info_frame, text=f"Місто: {weather['city']}, {weather['country']}", font=("Arial", 16, "bold"), bg="#FFFFFF").pack(anchor="w", padx=10, pady=5)
        tk.Label(self.city_info_frame, text=f"Опис: {weather['translated_description']}", font=("Arial", 12), bg="#FFFFFF").pack(anchor="w", padx=10)
        tk.Label(self.city_info_frame, text=f"Температура: {round(weather['temperature'])}°C", font=("Arial", 14), bg="#FFFFFF").pack(anchor="w", padx=10)
        tk.Label(self.city_info_frame, text=f"Відчувається як: {round(weather['feels_like'])}°C", font=("Arial", 12), bg="#FFFFFF").pack(anchor="w", padx=10, pady=5)

    # Оновлюю погодинний прогноз з іконками
    def update_current_forecast(self, forecast):
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()
        for i, item in enumerate(forecast):
            frame = tk.Frame(self.hourly_frame, bg="#F0F4F8", bd=1, relief="solid", width=80, height=100)
            frame.pack(side="left", padx=2, pady=2)
            frame.pack_propagate(False)
            tk.Label(frame, text=f"Час: {item['datetime'].strftime('%H:%M')}", font=("Arial", 8), bg="#F0F4F8", wraplength=80).pack(pady=2)
            tk.Label(frame, text=f"Темп.: {round(item['temperature'])}°C", font=("Arial", 10), bg="#F0F4F8").pack()
            day_time = "day" if 6 <= item["datetime"].hour < 20 else "night"
            icon_name = self.get_icon_name(item["description"], day_time)
            try:
                img_path = os.path.join("resources", "weather", f"{icon_name}.png")
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Файл {icon_name}.png не знайдено в {img_path}")
                img = Image.open(img_path).resize((40, 40), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(frame, image=photo, bg="#F0F4F8")
                icon_label.image = photo
                icon_label.pack(pady=2)
            except FileNotFoundError as e:
                print(f"Помилка: {e}")
                tk.Label(frame, text=f"[Відсутній: {icon_name}]", fg="#D32F2F", font=("Arial", 8), bg="#F0F4F8").pack(pady=2)
            except Exception as e:
                print(f"Помилка завантаження іконки {icon_name}: {e}")
                tk.Label(frame, text="[Помилка]", fg="#D32F2F", font=("Arial", 8), bg="#F0F4F8").pack(pady=2)

    # Оновлюю тижневий прогноз з іконками
    def update_current_weekly_forecast(self, weekly_forecast):
        for widget in self.weekly_frame.winfo_children():
            widget.destroy()
        for i, item in enumerate(weekly_forecast):
            frame = tk.Frame(self.weekly_frame, bg="#F0F4F8", bd=1, relief="solid")
            frame.pack(fill="x", padx=5, pady=2)
            desc = "ясне небо" if item["translated_description"] == "Ясне небо" else item["translated_description"]
            day_label = "Сьогодні" if i == 0 else "Завтра" if i == 1 else item["day"]
            tk.Label(frame, text=f"{day_label}: {desc}", font=("Arial", 12), bg="#F0F4F8").pack(side="left", padx=10)
            tk.Label(frame, text=f"День: {round(item['temperature_day'])}°C", font=("Arial", 12), bg="#F0F4F8").pack(side="left", padx=10)
            tk.Label(frame, text=f"Ніч: {round(item['temperature_night'])}°C", font=("Arial", 12), bg="#F0F4F8").pack(side="left", padx=10)
            day_time = "day"
            icon_name = self.get_icon_name(item["description"], day_time)
            try:
                img_path = os.path.join("resources", "weather", f"{icon_name}.png")
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Файл {icon_name}.png не знайдено в {img_path}")
                img = Image.open(img_path).resize((40, 40), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(frame, image=photo, bg="#F0F4F8")
                icon_label.image = photo
                icon_label.pack(side="left", padx=10)
            except FileNotFoundError as e:
                print(f"Помилка: {e}")
                tk.Label(frame, text=f"[Відсутній: {icon_name}]", fg="#D32F2F", font=("Arial", 8), bg="#F0F4F8").pack(side="left", padx=10)
            except Exception as e:
                print(f"Помилка завантаження іконки {icon_name}: {e}")
                tk.Label(frame, text="[Помилка]", fg="#D32F2F", font=("Arial", 8), bg="#F0F4F8").pack(side="left", padx=10)

    # Отримую назву іконки для погоди з JSON файлу
    def get_icon_name(self, description: str, day_time: str = "day") -> str:
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

    # Оновлюю графік для температури, вітру або вологості
    def update_graph(self, graph_type):
        if self.current_graph:
            self.current_graph.get_tk_widget().pack_forget()
            self.current_graph = None
        if not self.current_city:
            self.error_label.config(text="Спочатку виберіть місто у вкладці 'Погода'")
            return
        city = self.current_city
        forecast = self.weather_api.get_hourly_forecast(city)
        weekly_forecast = self.weather_api.get_weekly_forecast(city)
        if not forecast or not weekly_forecast:
            self.error_label.config(text="Не вдалося отримати дані для графіків")
            return
        fig, ax = plt.subplots(figsize=(10, 5))
        try:
            if graph_type == "temperature":
                hours = [item["datetime"].strftime("%H:%M") for item in forecast]
                temperatures = [item["temperature"] for item in forecast]
                feels_like = [item["feels_like"] for item in forecast]
                ax.plot(hours, temperatures, label="Температура", color="#FFA500", marker="o", linestyle="-")
                ax.plot(hours, feels_like, label="Відчувається", color="#0000FF", marker="x", linestyle="--")
                ax.set_xlabel("Година")
                ax.set_ylabel("Температура (°C)")
                ax.legend(loc="upper right")
                ax.tick_params(axis="x", rotation=45)
                ax.grid(True)
                all_temps = temperatures + feels_like
                min_temp = min(all_temps) - 1
                max_temp = max(all_temps) + 1
                ax.set_ylim(min_temp, max_temp)
                step = max(1, len(hours) // 8)
                ax.set_xticks(hours[::step])
            elif graph_type == "wind":
                hours = [item["datetime"].strftime("%H:%M") for item in forecast]
                wind_speeds = [item["wind_speed"] for item in forecast]
                ax.bar(hours, wind_speeds, label="Швидкість вітру", color="#4FC3F7")
                ax.set_xlabel("Година", fontfamily="Arial")
                ax.set_ylabel("Швидкість вітру (м/с)", fontfamily="Arial")
                ax.legend()
                ax.tick_params(axis="x", rotation=45)
                ax.grid(True, axis="y", linestyle="--", alpha=0.7)
                ax.set_facecolor("#F5F6F5")
                fig.patch.set_facecolor("#F5F6F5")
            elif graph_type == "humidity":
                days = [item["day"] for item in weekly_forecast]
                humidities = [item["humidity"] for item in weekly_forecast]
                city_info = self.weather_api.get_weather(city)
                city_name = city_info.get("city", "Невідомо")
                country = city_info.get("country", "Невідомо")
                explode = [0.1 if day in ["Субота", "Неділя"] else 0 for day in days]
                ax.pie(humidities, labels=days, autopct="%1.1f%%", startangle=90, explode=explode, colors=plt.cm.Pastel1.colors)
                ax.set_title(f"Вологість у {city_name}, {country}", fontfamily="Arial", pad=20)
                fig.patch.set_facecolor("#F5F6F5")
            self.current_graph = FigureCanvasTkAgg(fig, master=self.graphics_frame)
            self.current_graph.draw()
            self.current_graph.get_tk_widget().pack(pady=10, padx=10, fill="both", expand=True)
        except Exception as e:
            self.error_label.config(text=f"Помилка побудови графіку: {str(e)}")
            print(f"Помилка при оновленні графіку ({graph_type}): {str(e)}")
            plt.close(fig)

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()