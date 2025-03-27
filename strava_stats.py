from dotenv import load_dotenv
import os
import requests
import pandas as pd
import time
from datetime import datetime

load_dotenv(override=True)

class StravaAPI:
    def __init__(self):
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        self.access_token = None
        self.request_count = 0
        self.last_request_time = datetime.now()
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Brakuje wymaganych zmiennych środowiskowych!")
        
        self.get_access_token()
    
    def handle_rate_limit(self):
        self.request_count += 1
        
        if self.request_count >= 90:  # Bezpieczny margines przed limitem 100
            time_passed = (datetime.now() - self.last_request_time).total_seconds()
            if time_passed < 900:  # 15 minut w sekundach
                sleep_time = 900 - time_passed
                print(f"Osiągnięto limit zapytań. Oczekiwanie {sleep_time:.0f} sekund...")
                time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = datetime.now()
    
    def get_access_token(self):
        self.handle_rate_limit()
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(auth_url, data=payload)
        response.raise_for_status()
        self.access_token = response.json()['access_token']
        return self.access_token

    def get_activities(self, page=1, per_page=30):
        self.handle_rate_limit()
        if not self.access_token:
            self.get_access_token()
            
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'page': page, 'per_page': per_page}
        
        response = requests.get(activities_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_activity_details(self, activity_id):
        self.handle_rate_limit()
        if not self.access_token:
            self.get_access_token()
            
        activity_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = requests.get(activity_url, headers=headers)
        response.raise_for_status()
        return response.json()

def main():
    try:
        strava = StravaAPI()
        all_activities = []
        page = 5
        per_page = 50
        
        # Najpierw pobierz listę aktywności
        for current_page in range(1, page + 1):
            activities = strava.get_activities(page=current_page, per_page=per_page)
            if not activities:
                break
            all_activities.extend(activities)
            print(f"Pobrano stronę {current_page}, łącznie {len(all_activities)} aktywności")
        
        # Przetwórz pobrane aktywności
        detailed_activities = []
        for i, activity in enumerate(all_activities, 1):
            print(f"Pobieranie szczegółów aktywności {i}/{len(all_activities)}")
            details = strava.get_activity_details(activity['id'])
            
            # Wybierz tylko potrzebne pola
            clean_activity = {
                'name': details.get('name'),
                'type': details.get('type'),
                'start_date_local': details.get('start_date_local'),
                'distance': details.get('distance', 0) / 1000,
                'moving_time': details.get('moving_time'),
                'total_elevation_gain': details.get('total_elevation_gain'),
                'average_speed': details.get('average_speed', 0) * 3.6,
                'calories': details.get('calories'),
                'average_heartrate': details.get('average_heartrate'),
                'max_heartrate': details.get('max_heartrate')
            }
            detailed_activities.append(clean_activity)
        
        df = pd.DataFrame(detailed_activities)
        df.to_csv('recent_detailed_activities.csv', index=False)
        print(f"Zapisano {len(df)} aktywności")
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()