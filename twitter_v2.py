import random
import openai
import tweepy
import csv
import datetime
import os
import time
import logging
import tkinter as tk
from tkinter import messagebox, scrolledtext

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
valores_marca = "We focus on innovation, empowering entrepreneurs, and leveraging technology to create meaningful impact."

# File paths for storing tweets
TWEETS_FILE = "tweets_publicados.csv"

# Authenticate with the Twitter API v2
client = tweepy.Client(bearer_token=BEARER_TOKEN,
                       consumer_key=API_KEY,
                       consumer_secret=API_SECRET_KEY,
                       access_token=ACCESS_TOKEN,
                       access_token_secret=ACCESS_TOKEN_SECRET)

# Updated predefined topics and approaches with tones (in English)
temas = [
    "Daily Task Automation",
    "Useful AI Applications for Everyday Life",
    "Smart Home Automation (IoT)",
    "Online Security Tips",
    "Technology for Health Care",
    "Online Education: Accessible platforms for learning new tech skills",
    "Success Stories",
    "Healthcare",
    "Rising Companies and Growth",
    "How to Use AI to Our Advantage with Examples",
    "Daily Motivation to Keep Pursuing Our Goals",
    "Personal Finance",
    "How to Organize Your Day: Tips and Tricks",
    "Personal Development Through Technology",
    "Podcasting",
    "Digital Entrepreneurship"
]

enfoques = {
    "inspirational": [
        "Tell a success story in {tema}, focusing on the challenges and triumphs.",
        "Share an inspiring story about {tema} and its positive impact on daily life."
    ],
    "informative": [
        "Explain how {tema} can improve people's daily lives and why it's important.",
        "Provide a practical guide on {tema}, highlighting its benefits."
    ],
    "practical": [
        "Offer practical tips to implement {tema} in daily life.",
        "Explain how to start with {tema} in a simple and effective way."
    ]
}

# Fixed hashtags
fixed_hashtags = "#MamboDigital #MamboTrends"

# Helper function to check tweet length
def is_tweet_within_limit(tweet_text):
    return len(tweet_text) <= 280

# Helper function to truncate tweet text to fit within 280 characters including hashtags
def truncate_tweet_text(tweet_text, hashtags):
    total_limit = 280
    content_limit = total_limit - len(hashtags) - 1
    if len(tweet_text) > content_limit:
        truncated_text = tweet_text[:content_limit].rstrip() + '...'
        logging.info(f"Truncated tweet to fit within limit: {truncated_text}")
        return truncated_text + ' ' + hashtags
    return tweet_text + ' ' + hashtags

# Helper function to sanitize tweet text
def sanitize_tweet_text(tweet_text):
    return tweet_text.replace("\n", " ").strip()

# Function to select topic and approach based on random selection
def seleccionar_tema_y_enfoque():
    tema = random.choice(temas)
    enfoque_type = random.choice(list(enfoques.keys()))  # Randomly select an approach type (inspirational, informative, practical)
    enfoque = random.choice(enfoques[enfoque_type])
    return tema, enfoque, enfoque_type

# Function to generate text with OpenAI
def get_text(prompt, max_tokens=200):
    try:
        logging.debug(f"Sending prompt to OpenAI: {prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a highly professional and knowledgeable expert in technology, entrepreneurship, and leadership. Focus on providing value and creating engaging stories. Your values include: {valores_marca}."},
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

# Function to generate a tweet based on topic and approach
def generar_tweet():
    tema, enfoque, enfoque_type = seleccionar_tema_y_enfoque()
    
    prompt = enfoque.format(tema=tema)
    logging.info(f"Selected topic: {tema} ({enfoque_type})")
    logging.info(f"Selected approach: {enfoque}")

    try:
        text_response = get_text(prompt)
        logging.debug(f"Generated text: {text_response}")

        tweet_text = get_text(f"Summarize this story '{text_response}' into a concise, engaging tweet format that tells a complete story without asking questions or including calls to action.")
        tweet_text = sanitize_tweet_text(tweet_text.strip('"'))
        
        tweet_text = truncate_tweet_text(tweet_text, fixed_hashtags)

        if is_tweet_within_limit(tweet_text):
            logging.info(f"Tweet within limit: {tweet_text}")
            return tweet_text, tema, enfoque_type
        else:
            logging.warning(f"Tweet still exceeds limit after truncation: {tweet_text}")
            tweet_text = get_text(f"Summarize this further: {tweet_text} into a tweet of maximum 200 characters without hashtags.")
            tweet_text = sanitize_tweet_text(tweet_text.strip('"'))
            tweet_text = truncate_tweet_text(tweet_text, fixed_hashtags)

            if is_tweet_within_limit(tweet_text):
                logging.info(f"Further shortened tweet within limit: {tweet_text}")
                return tweet_text, tema, enfoque_type
            else:
                logging.error(f"Generated tweet still exceeds the limit after all attempts: {tweet_text}")
                return None, None, None

    except Exception as e:
        logging.error(f"Error generating content for '{tema}': {e}", exc_info=True)

    return None, None, None

# Function to publish the tweet
def publicar_tweet():
    tweet_text, tema, enfoque_type = generar_tweet()

    if tweet_text:
        success = False
        attempts = 0

        while not success and attempts < 3:
            try:
                response = client.create_tweet(text=tweet_text)
                tweet_id = response.data['id']
                logging.info(f"Tweet published: {tweet_text}")

                registrar_tweet(tweet_text, tema)
                success = True
                messagebox.showinfo("Success", "Tweet Published Successfully!")
            except tweepy.TooManyRequests as e:
                attempts += 1
                logging.error(f"Rate limit reached. Attempt {attempts} - retrying in 15 minutes...", exc_info=True)
                time.sleep(900)
            except tweepy.TweepyException as e:
                logging.error(f"Error posting tweet: {e}", exc_info=True)
                messagebox.showerror("Error", "Failed to publish tweet.")
                break
    else:
        logging.error("No tweet generated for publishing.")
        messagebox.showerror("Error", "No tweet generated for publishing.")

# Function to log the published tweet
def registrar_tweet(tweet_text, tema):
    with open(TWEETS_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.datetime.now(), tema, tweet_text])
    logging.info(f"Tweet logged to file.")

# Function to get the top 10 tweets based on likes and retweets
def obtener_top_tweets(user_id, num_tweets=100):
    try:
        response = client.get_users_tweets(id=user_id, tweet_fields=['public_metrics'], max_results=num_tweets)

        if response.data:
            tweets_data = []
            for tweet in response.data:
                tweet_text = tweet['text']
                likes = tweet['public_metrics']['like_count']
                retweets = tweet['public_metrics']['retweet_count']
                total_engagement = likes + retweets
                tweets_data.append({
                    "text": tweet_text,
                    "likes": likes,
                    "retweets": retweets,
                    "total_engagement": total_engagement
                })

            sorted_tweets = sorted(tweets_data, key=lambda x: x['total_engagement'], reverse=True)
            return sorted_tweets[:10]
        else:
            logging.error("No tweets found for the user.")
            return []

    except Exception as e:
        logging.error(f"Error fetching tweets: {e}", exc_info=True)
        return []

# Function to display the top 10 tweets in a scrollable window
def mostrar_ranking_tweets(user_id):
    top_tweets = obtener_top_tweets(user_id)

    if top_tweets:
        # Create a new window to display the top tweets
        ranking_window = tk.Toplevel()
        ranking_window.title("Top 10 Tweets by Engagement")
        
        text_area = scrolledtext.ScrolledText(ranking_window, wrap=tk.WORD, width=60, height=20)
        text_area.pack(pady=10)
        
        for i, tweet in enumerate(top_tweets, start=1):
            text_area.insert(tk.END, f"Rank {i}:\n")
            text_area.insert(tk.END, f"Text: {tweet['text']}\n")
            text_area.insert(tk.END, f"Likes: {tweet['likes']}, Retweets: {tweet['retweets']}\n")
            text_area.insert(tk.END, f"Total Engagement: {tweet['total_engagement']}\n\n")

        text_area.config(state=tk.DISABLED)
    else:
        messagebox.showerror("Error", "No tweets to display.")

# Tkinter GUI setup
def create_gui():
    root = tk.Tk()
    root.title("Twitter Bot")

    label = tk.Label(root, text="Press the button below to generate and publish a new tweet.")
    label.pack(pady=10)

    publish_button = tk.Button(root, text="Publish New Tweet", command=publicar_tweet, padx=20, pady=10)
    publish_button.pack(pady=20)

    ranking_button = tk.Button(root, text="Show Top 10 Tweets", command=lambda: mostrar_ranking_tweets("957786457669849088"), padx=20, pady=10)
    ranking_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
