from dotenv import load_dotenv
import os
import requests
import pandas as pd
from datetime import datetime

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv(override=True)

class StravaAPI:
    def __init__(self):
        """
        Inicjalizacja klienta Strava API używając zmiennych środowiskowych
        """
        # Pobierz dane uwierzytelniające z zmiennych środowiskowych
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        self.access_token = None
        
        # Sprawdź czy wszystkie wymagane zmienne są ustawione
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Brakuje wymaganych zmiennych środowiskowych!")
        
        # Od razu pobierz access token
        print("Inicjalizacja połączenia ze Stravą...")
        self.get_access_token()
        
    def get_access_token(self):
        """Pobiera nowy access token używając refresh tokena"""
        print("Pobieranie nowego access tokena...")
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(auth_url, data=payload)
            response.raise_for_status()  # Zgłosi wyjątek jeśli status != 200
            self.access_token = response.json()['access_token']
            print("Pomyślnie pobrano nowy access token")
            return self.access_token
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania access tokena: {e}")
            return None

    def get_activities(self, page=1, per_page=30):
        """Pobiera aktywności ze Stravy"""
        print(f"Pobieranie strony {page} aktywności...")
        
        if not self.access_token:
            if not self.get_access_token():
                return None
            
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'page': page, 'per_page': per_page}
        
        try:
            response = requests.get(activities_url, headers=headers, params=params)
            response.raise_for_status()
            activities = response.json()
            print(f"Pomyślnie pobrano {len(activities)} aktywności")
            return activities
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania aktywności: {e}")
            return None

def save_activities_to_csv(activities, filename='strava_activities.csv'):
    """Zapisuje aktywności do pliku CSV"""
    if not activities:
        print("Brak aktywności do zapisania")
        return
        
    # Przekształć listę aktywności w DataFrame
    df = pd.DataFrame(activities)
    
    # Wybierz najbardziej przydatne kolumny
    useful_columns = [
        'name', 'type', 'start_date_local', 'distance',
        'moving_time', 'elapsed_time', 'total_elevation_gain',
        'average_speed', 'max_speed', 'average_heartrate',
        'max_heartrate'
    ]

    # Wybierz tylko te kolumny, które istnieją w danych
    columns_to_use = [col for col in useful_columns if col in df.columns]
    df = df[columns_to_use]

    # Konwersja jednostek
    if 'distance' in df.columns:
        df['distance'] = df['distance'] / 1000  # na kilometry
        
    if 'average_speed' in df.columns:
        df['average_speed'] = df['average_speed'] * 3.6  # na km/h
        
    if 'max_speed' in df.columns:
        df['max_speed'] = df['max_speed'] * 3.6  # na km/h
    
    # Zapisz do CSV
    df.to_csv(filename, index=False)
    print(f"Zapisano aktywności do pliku {filename}")
    
    # Wyświetl podstawowe statystyki
    print("\nPodstawowe statystyki:")
    print(f"Liczba aktywności: {len(df)}")
    if 'distance' in df.columns:
        print(f"Całkowity dystans: {df['distance'].sum():.2f} km")
    if 'type' in df.columns:
        print("\nLiczba aktywności według typu:")
        print(df['type'].value_counts())

def main():
    try:
        # Utwórz instancję API
        strava = StravaAPI()
        
        # Pobierz aktywności
        activities = strava.get_activities(page=1, per_page=50)
        
        # Zapisz do pliku i wyświetl statystyki
        if activities:
            save_activities_to_csv(activities)
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()