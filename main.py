import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import requests
import tkinter as tk
from tkinter import ttk, messagebox


# Step 1: Get Coordinates from IP Address using ipinfo.io API
def get_ip_coordinates():
    try:
        ip_info = requests.get('https://ipinfo.io').json()
        location = ip_info['loc'].split(',')
        latitude = float(location[0])
        longitude = float(location[1])
        print(f"Fetched coordinates: Latitude: {latitude}, Longitude: {longitude}")
        return latitude, longitude
    except Exception as e:
        print("Error fetching coordinates:", e)
        return None, None


# Step 2: Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Step 3: Fetch coordinates and setup API request for weather data
def fetch_weather_data():
    latitude, longitude = get_ip_coordinates()
    if latitude is None or longitude is None:
        messagebox.showerror("Error", "Unable to fetch location coordinates.")
        return

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m",  # Request temperature data
        "forecast": "7",  # Requesting weather data for the next 7 days
        "timezone": "auto",  # Automatically detect timezone based on coordinates
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Debugging: Print the available methods and attributes of the response object
        print("Available methods and attributes of the response object:")
        print(dir(response))

        # Access the hourly data and get the first temperature value (we'll treat it as current)
        hourly = response.Hourly()
        hourly_time = pd.to_datetime(hourly.Time(), unit="s", utc=True)
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

        # Use the first hourly temperature as the "current" temperature
        current_temperature = hourly_temperature_2m[0]
        print(f"Current temperature: {current_temperature}°C")

        # Preset suggestions based on temperature
        if current_temperature > 25:
            weather_suggestion = "It's sunny and warm! Wear sunglasses."
        elif current_temperature < 10:
            weather_suggestion = "It's cold! Wear a jacket."
        else:
            weather_suggestion = "Mild weather today, enjoy!"

        # Display current weather in the UI
        label_current_weather.config(text=f"Current Temperature: {current_temperature}°C\n"
                                        f"Recommendation: {weather_suggestion}")

        # Process hourly forecast data for the next 7 days (every 2 hours)
        hourly_dataframe = pd.DataFrame({
            "datetime": hourly_time,
            "temperature_2m": hourly_temperature_2m,
        })

        hourly_dataframe = hourly_dataframe.set_index("datetime")
        hourly_dataframe.index.name = "Date/Time"

        # Filter data to include every 2 hours
        hourly_dataframe = hourly_dataframe[hourly_dataframe.index.hour % 2 == 0]

        # Display hourly forecast in the UI
        text_hourly_forecast.config(state=tk.NORMAL)  # Enable editing
        text_hourly_forecast.delete(1.0, tk.END)  # Clear the previous forecast
        text_hourly_forecast.insert(tk.END, hourly_dataframe.to_string())
        text_hourly_forecast.config(state=tk.DISABLED)  # Disable editing

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        messagebox.showerror("Error", "Failed to fetch weather data. Please try again.")


# Step 4: Create a basic Tkinter UI
root = tk.Tk()
root.title("Weather App")
root.geometry("600x600")

# Current weather display
frame_current_weather = ttk.LabelFrame(root, text="Current Weather", padding="10")
frame_current_weather.pack(padx=10, pady=10, fill="x", expand=True)

label_current_weather = tk.Label(frame_current_weather, text="Fetching weather data...", font=("Arial", 12))
label_current_weather.pack(padx=10, pady=10)

# Hourly forecast display
frame_hourly_forecast = ttk.LabelFrame(root, text="7-Day Hourly Forecast (Every 2 Hours)", padding="10")
frame_hourly_forecast.pack(padx=10, pady=10, fill="both", expand=True)

text_hourly_forecast = tk.Text(frame_hourly_forecast, wrap="none", height=10, font=("Courier", 10))
text_hourly_forecast.config(state=tk.DISABLED)
text_hourly_forecast.pack(padx=10, pady=10, fill="both", expand=True)

# Fetch weather button
button_fetch_weather = ttk.Button(root, text="Fetch Weather", command=fetch_weather_data)
button_fetch_weather.pack(pady=10)

# Start the Tkinter event loop
root.mainloop()
