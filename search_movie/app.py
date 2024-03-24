import streamlit as st
from google.cloud import bigquery
import os
import requests
from PIL import Image 
import base64
import io

#Connect to the google cloud when runing locally 
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "JSON_KEY.json"
client = bigquery.Client(project="cloud-advanced-analytics-1")

#IN THIS SECTION THERE IS ALL THE PYTHON FUNCTIONS AND BIG QUERY FUNCTIONS

#function to get the autocomplete on the research toolbar 
def get_autocomplete_titles(user_input):
    query = f"""
    SELECT title, tmdbId FROM `cloud-advanced-analytics-1.assignment1.movies`
    WHERE LOWER(title) LIKE LOWER('{user_input}%')
    ORDER BY title ASC
    LIMIT 10
    """
    query_job = client.query(query)
    results = query_job.result()
    return [(row.title, row.tmdbId) for row in results]

#Calls the google cloud function to get the information of the film 
def get_movie_details_from_cloud_function(movie_id):
    cloud_function_url = "https://europe-west6-cloud-advanced-analytics-1.cloudfunctions.net/movie_details"
    params = {"movie_id": str(movie_id)}
    try:
        response = requests.get(cloud_function_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error retrieving film details: {e}")
        return None

# Here ther are different functions for querying the database and retrieving films based on the language, genres
def get_movies_by_language(language):
    query = f"""
    SELECT title, tmdbId FROM `cloud-advanced-analytics-1.assignment1.movies`
    WHERE LOWER(language) = LOWER('{language}')
    ORDER BY title ASC
    LIMIT 25
    """
    query_job = client.query(query)
    results = query_job.result()
    return [(row.title, row.tmdbId) for row in results]

def get_movies_by_genres(genre):
    query = f"""
    SELECT title, tmdbId FROM `cloud-advanced-analytics-1.assignment1.movies`
    WHERE LOWER(genres) = LOWER('{genre}')
    ORDER BY title ASC
    LIMIT 25
    """
    query_job = client.query(query)
    results = query_job.result()
    return [(row.title, row.tmdbId) for row in results]

#This is used to add the different language, genres and rating available for the differents filters
def get_available_languages():
    query = """
    SELECT DISTINCT language 
    FROM `cloud-advanced-analytics-1.assignment1.movies` 
    ORDER BY language
    """
    try:
        query_job = client.query(query)
        results = query_job.result()
        return [row.language for row in results]
    except Exception as e:
        st.error(f"Error retrieving languages : {e}")
        return []  
    

def get_available_genres():
    query = """
    SELECT DISTINCT genres
    FROM `cloud-advanced-analytics-1.assignment1.movies`
    ORDER BY genres
    """
    query_job = client.query(query)
    results = query_job.result()
    return [row.genres for row in results]

def get_available_rating():
    query = """
    SELECT DISTINCT rating
    FROM `cloud-advanced-analytics-1.assignment1.ratings`
    ORDER BY rating
    """
    query_job = client.query(query)
    results = query_job.result()
    return [row.rating for row in results]


#Function who display the movies in the advanced research
def get_filtered_movies(language, genre, release_year_after, min_average_rating):
    language_filter = "" if language == "See all languages" else f"AND LOWER(m.language) = LOWER('{language}')"
    
    genre_filter = "" if genre == "See all genres" else f"AND LOWER(m.genres) LIKE LOWER('%{genre}%')"
    
    query = f"""
    SELECT m.title, m.tmdbId, AVG(r.rating) AS average_rating
    FROM `cloud-advanced-analytics-1.assignment1.movies` m
    LEFT JOIN `cloud-advanced-analytics-1.assignment1.ratings` r ON m.movieId = r.movieId
    WHERE m.release_year > {release_year_after}
    {language_filter}
    {genre_filter}
    GROUP BY m.title, m.tmdbId
    HAVING AVG(r.rating) >= {min_average_rating}
    ORDER BY average_rating DESC, m.title ASC
    LIMIT 25
    """
    query_job = client.query(query)
    results = query_job.result()
    return [(row.title, row.tmdbId, row.average_rating) for row in results]



#Streamlit design 

st.title("Search movie ")

    
st.title(f"***Simple research***")

#UI for the simple research section (research toolbar)
if 'user_input' not in st.session_state or 'selected_movie_id' not in st.session_state:
    st.session_state['user_input'] = ''
    st.session_state['selected_movie_id'] = None
    st.session_state['selected'] = False

user_input = st.text_input("Enter a movie name", value=st.session_state['user_input'])

if user_input=='':
    st.session_state['selected_movie_id'] = None
    st.session_state['selected'] = False

if user_input and not st.session_state['selected']:
    suggestions = get_autocomplete_titles(user_input)
    if suggestions: 
        for title, movieId in suggestions:
            if st.button(title, key=title):
                st.session_state['user_input'] = title  
                st.session_state['selected_movie_id'] = movieId
                st.session_state['selected'] = True
                st.experimental_rerun()
    else: 
        st.write("NO RESULST FOUND")

else:
    st.session_state['selected'] = False 

if 'selected_movie_id' in st.session_state and st.session_state['selected_movie_id']:
    movie_details = get_movie_details_from_cloud_function(st.session_state['selected_movie_id'])
    if movie_details:
        col1, col2 = st.columns(2)
        with col1:
            if movie_details['movie_poster']:
                st.image(movie_details['movie_poster'], width=200)
            else:
                st.image('poster not available.jpg', width=300)

        with col2:
            st.write(f"**Movie name :** {movie_details['movie_name']}")
            st.write(f"**Release date :** {movie_details['release_date']}")
            st.write(f"**Synopsis :** {movie_details['synopsis']}")
            st.write(f"**TMDB average grade :** {movie_details['average_rating']}")
            trailers = movie_details.get('trailers', [])
            if trailers:
                st.write("**Trailer :**")
                st.video(trailers[0])
            else:
                st.write("**Trailer :** Trailer not available for the moment")

st.markdown('<hr style="border:2px solid gray; margin-bottom: 20px;"/>', unsafe_allow_html=True)

#UI for the advanced section (differents filter)
st.title(f"***Advanced research***")

languages = ["See all languages"] + get_available_languages()  
genres = ["See all genres"] + get_available_genres()  
selected_language = st.selectbox('Select the language', languages)
selected_genre = st.selectbox('Select the genre', genres)

col1, col2 = st.columns(2)
with col1:
    release_year_after = st.slider("Release year after:", 1900, 2024, 2000, 1)
with col2:
    min_average_rating = st.slider("Minimum average grade:", 0.0, 5.0, 3.0, 0.1)
    


if st.button('Display movies'):
    movies = get_filtered_movies(selected_language, selected_genre, release_year_after, min_average_rating)
    st.markdown('<hr style="border:2px solid gray; margin-bottom: 20px;"/>', unsafe_allow_html=True)

    if movies:
        for title, tmdbId, _ in movies:  
            with st.expander(f"{title}"):  
                movie_details = get_movie_details_from_cloud_function(tmdbId)
                if movie_details:
                    col1, col2 = st.columns(2)
                    with col1:
                        if movie_details.get('movie_poster'):
                            st.image(movie_details['movie_poster'], width=200)
                        else:
                            st.image('poster not available.jpg', width=300)
                    with col2:
                        st.write(f"**Movie name :** {movie_details['movie_name']}")
                        st.write(f"**Release date :** {movie_details['release_date']}")
                        st.write(f"**Synopsis :** {movie_details['synopsis']}")
                        st.write(f"**TMDB average grade :** {movie_details['average_rating']}")
                        trailers = movie_details.get('trailers', [])
                        if trailers:
                            st.write("**Trailer :**")
                            st.video(trailers[0])
                        else:
                            st.write("Trailer not available for the moment")
                else:
                    st.error(f"Movie details of  {title} cannot be uploaded.")
    else:
        st.error("No film corresponding to the criteria.")

