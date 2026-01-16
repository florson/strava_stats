from dotenv import load_dotenv
import os
import sys
import pandas as pd
import datetime
from openai import OpenAI

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ATHLETE_DATA = {
    "gender": "mężczyzna",
    "age": 35,
    "weight": 73, 
    "goal": "optymalizacja formy pod kątem startów w maratonach MTB o długości do około 30 km i 1000m wzniesienia"
}

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

def generate_insights(data):
    prompt = f"""
    Dane podopiecznego:
    Płeć: {ATHLETE_DATA['gender']}
    Wiek: {ATHLETE_DATA['age']}
    Waga: {ATHLETE_DATA['weight']}kg

    Dane z treningów: {data}

    Przygotuj krótkie podsumowanie do dashboardu z danymi. Wybierz najciekawsze lub najbardziej wartościowe dane, zarówno z treningów jak i startów zawodach. 
    Jako przykład, posłuż się takim podsumowaniem:
    "### Podsumowanie wyników treningów

    #### Analiza treningów:
    - **Największa odległość**: 93.1 km (9.05.2024), z czasem **2 godzi 54 minuty**, średnia prędkość 31.99 km/h.
    - **Najwyższa średnia prędkość**: 32.28 km/h (13.08.2024) na dystansie **74.9 km**.
    - **Największe przewyższenie**: 1095 m (19.10.2024), przy dystansie **54.3 km**."
    Rozwiń po prostu punkt "analiza trenigów". Nie bierz pod uwagę danych, które mogą być błędne - np. maksymalne tętno powyżej 190.
    Nie używaj znaków "#" czy "*" w odpowiedzi.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "Jesteś trenerem kolarstwa, który ma za zadanie przeanalizować dane przekazane przez swojego podopiecznego oraz jego wyniki sportowe"},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating insights: {e}")
        return "Error generating insights. Please check your OpenAI API key and connection."

def main():
    try:
        df = pd.read_csv("recent_detailed_activities.csv")

        df.drop(columns="name", inplace=True)
        df = df[df['type']=='Ride']

        df_json = df.to_json(orient='records')
        
        insights = generate_insights(df_json)
        
        with open("insights.csv", "w", encoding='utf-8') as file:
            file.write(insights)

        print("Insights and summaries saved successfully.")
        
    except FileNotFoundError:
        print("Error: Could not find the recent_detailed_activities.csv file.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()