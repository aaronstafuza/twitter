import random
import openai
import tweepy
import csv
import datetime
import json
import os
import time
import logging
import requests
from collections import deque

# Set up logging
logging.basicConfig(filename='tweet_bot.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API keys from environment variables
openai.api_key = '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'

API_KEY = 'fsNAS45dukwqmXWLPsuykw68q'
API_SECRET_KEY = '8IYY5g0xbicnkIdO6QHnpyDLLpCTO1TWNZzKiKCPPqY77LE8BA'

ACCESS_TOKEN = '957786457669849088-fhbP48ffGlovikNUFNiZzhkzsjFDK4H'
ACCESS_TOKEN_SECRET = 'lrNsFeM4p5aEmRRIytFrNaHum1bPnrpPivxOhUzaLxhp8'

BEARER_TOKEN='AAAAAAAAAAAAAAAAAAAAAN8kvgEAAAAAKryPVU%2FD9iWNXmwon5PVczpNpcA%3Dlkos3xnbhM1dljiKeXSNh9ADZKN0uyP2G3w1zDDa8Cg0PX3shT'

# Define brand values
VALORES_MARCA = "We focus on innovation, empowering entrepreneurs, and leveraging technology to create meaningful impact."

# File paths for storing tweets and scores
TWEETS_FILE = "tweets_publicados.csv"
SCORES_FILE = "scores.json"

# Authenticate with the Twitter API v2
client = tweepy.Client(bearer_token=BEARER_TOKEN,
                       consumer_key=API_KEY,
                       consumer_secret=API_SECRET_KEY,
                       access_token=ACCESS_TOKEN,
                       access_token_secret=ACCESS_TOKEN_SECRET)

# Expanded topics and approaches
TEMAS = [
    "technology trends shaping our future",
    "the impact of artificial intelligence on startups",
    "success stories in tech entrepreneurship",
    "latest innovations disrupting industries",
    "key lessons from successful entrepreneurs",
    "how startups are driving societal change",
    "insights from tech leaders",
    "cybersecurity in the modern era",
    "emerging tech in 2024",
    "sustainability in tech"
]

ENFOQUES = {
    "inspirational": [
        "Tell a success story in {tema}, focusing on the challenges and the triumphs.",
        "Share an inspiring story about {tema} and its impact on the world.",
    ],
    "informative": [
        "Explain the latest developments in {tema}, and why they matter.",
        "Provide a detailed analysis of {tema} and its potential impact.",
        "Highlight the key players in {tema} and their contributions.",
    ],
    "analytical": [
        "Explore the trends in {tema}, focusing on the data and forecasts.",
        "Analyze the implications of {tema} on the industry and society.",
        "Discuss the potential future developments in {tema}.",
    ],
    "statistical": [
        "Share the latest statistics on {tema} and what they mean.",
        "Break down the data trends in {tema}, explaining their significance.",
        "Highlight surprising data about {tema}."
    ],
    "visual": [
        "Create an infographic about {tema} highlighting the key trends.",
        "Share a chart or graph illustrating the impact of {tema}.",
        "Use a visual metaphor to explain {tema}."
    ]
}

# Fixed hashtags
FIXED_HASHTAGS = "#MamboDigital #MamboTrends"

# Circular buffer to avoid repeating topics
recent_topics = deque(maxlen=5)

def retry_on_exception(retries=3, delay=5, backoff=2):
    def retry_decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    logging.warning(f"Retry {attempt}/{retries} after exception: {e}")
                    time.sleep(delay)
                    delay *= backoff
            logging.error(f"Failed after {retries} retries.")
            return None
        return wrapper
    return retry_decorator

def is_tweet_within_limit(tweet_text):
    return len(tweet_text) <= 280

def truncate_tweet_text(tweet_text, hashtags):
    total_limit = 280
    content_limit = total_limit - len(hashtags) - 1
    if len(tweet_text) > content_limit:
        truncated_text = tweet_text[:content_limit].rstrip() + '...'
        logging.info(f"Truncated tweet to fit within limit: {truncated_text}")
        return truncated_text + ' ' + hashtags
    return tweet_text + ' ' + hashtags

def sanitize_tweet_text(tweet_text):
    return tweet_text.replace("\n", " ").strip()

def cargar_puntajes():
    if not os.path.exists(SCORES_FILE):
        scores = {"temas": {}, "enfoques": {}}
        guardar_puntajes(scores)
    else:
        with open(SCORES_FILE, 'r') as file:
            scores = json.load(file)
    return scores

def guardar_puntajes(scores):
    with open(SCORES_FILE, 'w') as file:
        json.dump(scores, file)
    logging.info(f"Puntajes guardados en {SCORES_FILE}")

def actualizar_puntajes(tema, enfoque, likes, retweets, scores):
    puntaje = likes + (retweets * 2)
    update_scores(scores, "temas", tema, puntaje)
    update_scores(scores, "enfoques", enfoque, puntaje)
    guardar_puntajes(scores)

def update_scores(scores, category, key, value):
    scores[category][key] = scores[category].get(key, 0) + value

def seleccionar_tema_y_enfoque(scores):
    # Choose a topic that hasn't been used recently
    tema = None
    while tema is None or tema in recent_topics:
        tema = max(scores["temas"], key=scores["temas"].get) if scores["temas"] else random.choice(TEMAS)
    
    # Add the selected topic to the recent topics buffer
    recent_topics.append(tema)

    enfoque_type = random.choice(list(ENFOQUES.keys()))
    enfoque = random.choice(ENFOQUES[enfoque_type])
    return tema, enfoque, enfoque_type

def fetch_external_content():
    try:
        response = requests.get('https://api.your-news-source.com/latest-tech-news')
        news_data = response.json()
        headline = news_data['articles'][0]['title']
        return headline
    except Exception as e:
        logging.error(f"Error fetching external content: {e}")
        return None

def get_text(prompt, max_tokens=200):
    try:
        logging.debug(f"Sending prompt to OpenAI: {prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a highly professional and knowledgeable expert in technology, entrepreneurship, and leadership. Focus on providing value and creating engaging stories. Your values include: {VALORES_MARCA}."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0.5,
            presence_penalty=0.6
        )
        logging.debug(f"OpenAI response received: {response}")
        
        if response.choices and response.choices[0].message['content']:
            return response.choices[0].message['content'].strip().strip('"')
        else:
            logging.error("No valid response received from OpenAI API")
            return "No valid response received from OpenAI API"
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}", exc_info=True)
        return "OpenAI API error"
    except Exception as e:
        logging.error(f"Unexpected error during OpenAI API call: {e}", exc_info=True)
        return "Unexpected error during OpenAI API call"

def generar_tweet(scores):
    tema, enfoque, enfoque_type = seleccionar_tema_y_enfoque(scores)
    external_content = fetch_external_content()
    
    if external_content:
        prompt = f"{enfoque.format(tema=tema)} Include this information: {external_content}"
    else:
        prompt = enfoque.format(tema=tema)
    
    logging.info(f"Tema seleccionado: {tema} ({enfoque_type})")
    logging.info(f"Enfoque seleccionado: {enfoque}")

    try:
        text_response = get_text(prompt)
        logging.debug(f"Texto generado: {text_response}")

        tweet_text = get_text(f"Summarize this story '{text_response}' into a concise, engaging tweet format that tells a complete story without asking questions or including calls to action.")
        tweet_text = sanitize_tweet_text(tweet_text.strip('"'))
        tweet_text = truncate_tweet_text(tweet_text, FIXED_HASHTAGS)

        if is_tweet_within_limit(tweet_text):
            logging.info(f"Tweet within limit: {tweet_text}")
            return tweet_text, tema, enfoque_type
        else:
            logging.warning(f"Tweet still exceeds limit after truncation: {tweet_text}")
            tweet_text = get_text(f"Summarize this further: {tweet_text} into a tweet of maximum 200 characters without hashtags.")
            tweet_text = sanitize_tweet_text(tweet_text.strip('"'))
            tweet_text = truncate_tweet_text(tweet_text, FIXED_HASHTAGS)

            if is_tweet_within_limit(tweet_text):
                logging.info(f"Further shortened tweet within limit: {tweet_text}")
                return tweet_text, tema, enfoque_type
            else:
                logging.error(f"Generated tweet still exceeds the limit after all attempts: {tweet_text}")
                return None, None, None

    except Exception as e:
        logging.error(f"Error generating content for '{tema}': {e}", exc_info=True)

    return None, None, None

@retry_on_exception(retries=3, delay=5, backoff=2)
def publicar_tweet():
    scores = cargar_puntajes()
    tweet_text, tema, enfoque_type = generar_tweet(scores)

    if tweet_text:
        success = False
        attempts = 0

        while not success and attempts < 3:  # Retry up to 3 times
            try:
                response = client.create_tweet(text=tweet_text)
                tweet_id = response.data['id']
                logging.info(f"Tuit publicado: {tweet_text}")

                # Delay to allow Twitter to update metrics
                time.sleep(10)

                likes, retweets = obtener_metricas(tweet_id)
                actualizar_puntajes(tema, enfoque_type, likes, retweets, scores)
                registrar_tweet(tweet_text, tema, likes, retweets)
                success = True
            except tweepy.TooManyRequests as e:
                attempts += 1
                logging.error(f"Rate limit reached. Attempt {attempts} - retrying in 15 minutes...", exc_info=True)
                time.sleep(900)  # Wait for 15 minutes before retrying
            except tweepy.TweepyException as e:
                logging.error(f"Error tweeting: {e}", exc_info=True)
                break
    else:
        logging.error("No tweet generated to publish.")

def obtener_metricas(tweet_id):
    try:
        tweet = client.get_tweet(tweet_id, tweet_fields=['public_metrics'])
        likes = tweet.data['public_metrics']['like_count']
        retweets = tweet.data['public_metrics']['retweet_count']
        return likes, retweets
    except Exception as e:
        logging.error(f"Error fetching tweet metrics for tweet_id {tweet_id}: {e}", exc_info=True)
        return 0, 0

def registrar_tweet(tweet_text, tema, likes, retweets):
    try:
        with open(TWEETS_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.datetime.now(), tema, tweet_text, likes, retweets])
        logging.info("Tweet registered in the file.")
    except Exception as e:
        logging.error(f"Error registering tweet: {e}", exc_info=True)

if __name__ == "__main__":
    publicar_tweet()
