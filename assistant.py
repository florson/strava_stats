from dotenv import load_dotenv
import os
import sys
import pandas as pd
import datetime
from openai import OpenAI

# API Key OpenAI
load_dotenv(override=True)

# Create OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Hardcoded athlete data
ATHLETE_DATA = {
    "gender": "mężczyzna",
    "age": 35,
    "weight": 73,  # in kilograms
    "goal": "optymalizacja formy pod kątem startów w maratonach MTB o długości do około 30 km i 1000m wzniesienia"
}

# Function to analyze activities
def analyze_activities(df):
    if df.empty:
        return {}
        
    summary = {}
    activity_types = df["type"].unique()
    
    for activity in activity_types:
        filtered = df[df["type"] == activity]
        summary[activity] = {
            "average_heart_rate": filtered["average_heartrate"].mean() if "average_heartrate" in filtered else 0,
            "total_calories": filtered["calories"].sum() if "calories" in filtered else 0,
            "total_distance": filtered["distance"].sum() if "distance" in filtered.columns else 0,
            "total_elevation": filtered["total_elevation_gain"].sum() if "total_elevation_gain" in filtered.columns else 0,
        }
    return summary

# Function to generate insights
def generate_insights(data):
    prompt = f"""
    Dane podopiecznego:
    Płeć: {ATHLETE_DATA['gender']}
    Wiek: {ATHLETE_DATA['age']}
    Waga: {ATHLETE_DATA['weight']}kg

    Zawodnik startował w następujących maratonach MTB:
    1. 12.05.2024, miejsce 23/56
    2. 26.05.2024, miejsce 22/48
    3. 01.09.2024, miejsce 33/73
    4. 28.09.2024, miejsce 20/45
    5. 05.10.2024, miejsce 16/46
    6. 26.10.2024, miejsce 17/43

    Dane z treningów: {data}

    Przygotuj krótkie podsumowanie do dashboardu z danymi. Wybierz najciekawsze lub najbardziej wartościowe dane, zarówno z treningów jak i startów zawodach. 
    Jako przykład, posłuż się takim podsumowaniem:
    "### Podsumowanie wyników treningów i startów (35 lat, 73 kg)

    #### Wyniki startów w maratonach MTB:
    1. **12.05.2024**: Miejsce 23/56
    2. **26.05.2024**: Miejsce 22/48
    3. **01.09.2024**: Miejsce 33/73
    4. **28.09.2024**: Miejsce 20/45
    5. **05.10.2024**: Miejsce 16/46
    6. **26.10.2024**: Miejsce 17/43

    **Najlepszy wynik**: Miejsce 16/46 - 05.10.2024

    #### Analiza treningów:
    - **Największa odległość**: 93.1 km (9.05.2024), z czasem **2 godzi 54 minuty**, średnia prędkość 31.99 km/h.
    - **Najwyższa średnia prędkość**: 32.28 km/h (13.08.2024) na dystansie **74.9 km**.
    - **Największe przewyższenie**: 1095 m (19.10.2024), przy dystansie **54.3 km**."
    Rozwiń po prostu punkt "analiza trenigów". Nie bierz pod uwagę danych, które mogą być błędne - np. maksymalne tętno powyżej 190.
    Nie używaj znaków "#" czy "*" w odpowiedzi.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Jesteś trenerem kolarstwa, który ma za zadanie przeanalizować dane przekazane przez swojego podopiecznego oraz jego wyniki sportowe"},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating insights: {e}")
        return "Error generating insights. Please check your OpenAI API key and connection."

# Main logic
def main():
    try:
        # Load CSV from strava_stats
        df = pd.read_csv("recent_detailed_activities.csv")
        '''
        # Convert 'data' column to datetime and ensure tz-naive
        df["start_date_local"] = pd.to_datetime(df["start_date_local"]).dt.tz_localize(None)
        
        reference_date = datetime.datetime(2025, 1, 1)
        
        # Calculate date ranges
        last_week_start = reference_date - datetime.timedelta(days=7)
        last_month_start = reference_date - datetime.timedelta(days=30)
        year_start = datetime.datetime(reference_date.year, 1, 1)
        
        # Filter data by date ranges
        last_week_df = df[(df["start_date_local"] >= last_week_start) & (df["start_date_local"] <= reference_date)]
        last_month_df = df[(df["start_date_local"] >= last_month_start) & (df["start_date_local"] <= reference_date)]
        yearly_df = df[(df["start_date_local"] >= year_start) & (df["start_date_local"] <= reference_date)]
        
        # Summarize and analyze data
        last_week_summary = analyze_activities(last_week_df)
        last_month_summary = analyze_activities(last_month_df)
        yearly_summary = analyze_activities(yearly_df)
        '''
        df.drop(columns="name", inplace=True)
        df = df[df['type']=='Ride']

        df_json = df.to_json(orient='records')
        
        insights = generate_insights(df_json)
        
        # Save insights to text file
        with open("insights.csv", "w", encoding='utf-8') as file:
            file.write(insights)
        '''
        # Convert summaries to a format that can be saved to CSV
        summaries_df = pd.DataFrame({
            'period': ['last_week', 'last_month', 'year'],
            'summary': [last_week_summary, last_month_summary, yearly_summary]
        })
        summaries_df.to_csv("summaries.csv", index=False)
        '''
        print("Insights and summaries saved successfully.")
        
    except FileNotFoundError:
        print("Error: Could not find the recent_detailed_activities.csv file.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()