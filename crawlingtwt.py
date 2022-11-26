import tweepy
import re
import pandas as pd
import string
import csv
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
from nltk.tokenize import word_tokenize
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st 
import altair as alt
import Sastrawi

st.header("Sentimen Analysis Twitter")

showWarningOnDirectExecution = False
showErrorDetails = False
showTracebacks = False

api_key = "earScsYmfXq5tOUpzEziXxKwt"
api_key_secret = "C6VouJVg0UUahbSqasFQAcRUE3dNdnaZFamS9zrXnp4cqOvAyP"
access_token = "66106451-UFbSuHUjKFViuD5RaW3B14AIMmzlEcuEMFK4xrZCu"
access_token_secret = "xw78fGFsSmdX3KXZpHIgcU03yK64gxoYfZ2lfjhyZ5stU"

auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)


keyword = st.text_input(label="**Masukan keyword** 👇 ")
naOfTweet = st.number_input(label='Jumlah tweet untuk di analisa: ',value=0)
tweets = tweepy.Cursor(api.search_tweets, q=keyword, lang='id').items(naOfTweet)
tweet_list = []
tweet_user = []
tweet_id = []
tweet_loc = []

for tweet in tweets:
#   print(tweet.text)
  tweet_list.append(tweet.text)
  tweet_user.append(tweet.user.screen_name)
  tweet_id.append(tweet.user.id)
  tweet_loc.append(tweet.user.location)


dictTweets = {'waktu':tweet_loc,'id':tweet_id,'username':tweet_user,'tweet':tweet_list}
df = pd.DataFrame(dictTweets, columns=['username','tweet'])

# Membersihkan tweet
if keyword == '':
    if naOfTweet == 0:
        None
if keyword != '':
    if naOfTweet != 0:
        dictTweets = pd.DataFrame(tweet_list)
        dictTweets["text"] = dictTweets[0]
        def clean_text(text):
            text = str(text).lower()
            text = re.sub('@[^\s]+','',text)
            text = re.sub('rt', '', text)
            text = re.sub('\[.*?\]', '', text)
            text = re.sub('https?://\S+|www\.\S+', '', text)
            text = re.sub('<.*?>+', '', text)
            text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
            text = re.sub('\n', '', text)
            text = re.sub('\w*\d\w*', '', text)
            text = re.sub(' +', ' ', text)
            return text


        dictTweets['text'] = dictTweets['text'].apply(lambda x:clean_text(x))
        df_fix=pd.DataFrame(dictTweets['text'])

        #Membuang data duplikat

        df_fix.drop_duplicates(inplace=True)

        # fungsi tokenisasi (Memecah kalimat menjadi beberapa kata)

        def tokenizingText(text):
            text = word_tokenize(text)
            return text
        
        import nltk
        nltk.download('punkt')
        from nltk.corpus import stopwords
        nltk.download('stopwords')

        from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
        # stop_factory = StopWordRemoverFactory()
        def filteringText(text): # Remove stopwors in a text
            listStopwords = stopwords.words('indonesian')
            listStopwords.extend(['dengan', 'ia','bahwa','oleh', keyword.lower(),'aku', 'kamu'
                                    'list',' " ','ya','yuk','kak','yg','po','gak',
                                    'ke','bgt','lg','gw','aja','gini','wik','kalo','ga',
                                    'dom','yah','gada','nya','jdi','sih','gue','gua','dah',
                                    'ni','lu','ayo','vs','v'])
            listStopwords = set(listStopwords)
            filtered = []
            for txt in text:
                if txt not in listStopwords:
                    filtered.append(txt)
            text = filtered             
            return text
        
        df_fix['text_preprocessed'] = df_fix['text'].apply(tokenizingText)
        df_fix['text_preprocessed'] = df_fix['text_preprocessed'].apply(filteringText)

        # Memasukan kamus (kata positif & negatif)
        lexicon_positive = dict()
        import csv
        with open('positive_lex.csv', 'r') as csvfile:
            pos_word = csv.reader(csvfile, delimiter=',')
            next(pos_word, None)
            for row in pos_word:
                lexicon_positive[row[0]] = int(row[1])

        lexicon_negative = dict()
        import csv
        with open('negatif_lex.csv', 'r') as csvfile:
            neg_word = csv.reader(csvfile, delimiter=',')
            next(neg_word, None)
            for row in neg_word:
                lexicon_negative[row[0]] = int(row[1])



        # Fungsi analisis secara perulangan

        def sentiment_analysis(text):
            score = 0
            for word in text:
                if (word in lexicon_positive):
                    score = score + lexicon_positive[word]
            for word in text:
                if (word in lexicon_negative):
                    score = score + lexicon_negative[word]
            sentimen=''
            if (score > 0):
                sentimen = 'positive'
            elif (score < 0):
                sentimen = 'negative'
            else:
                sentimen = 'neutral'
            return score, sentimen

        # Menghitung jumlah tweet bersifat negatif, positif, & neutral
        import time
        with st.spinner('Wait for it...'):
            time.sleep(5)
            st.success('Done!')
        results = df_fix['text_preprocessed'].apply(sentiment_analysis)
        results = list(zip(*results))
        df_fix['sentimen_score'] = results[0]
        df_fix['sentimen'] = results[1]
        calculate = df_fix['sentimen'].value_counts()
        st.write(calculate)

        # st.bar_chart(calculate, width=50)
        # st.bar_chart(x='sentimen', data=df_fix)
        # plt.figure(figsize=(12,6))
        # sns.countplot(x='sentimen',data=df_fix)


        # Membuat dataframe tweet sesuai dengan sentimen
        df_fix['text_preprocessed']=df_fix['text_preprocessed'].apply(', '.join)
        df_fix_neutral = df_fix[df_fix["sentimen"] == 'neutral']
        df_fix_positive = df_fix[df_fix["sentimen"] == 'positive']
        df_fix_negative = df_fix[df_fix["sentimen"] == 'negative']

        
        #Function to Create Wordcloud Neutral
        def create_wordcloud_neutral(text):
            #mask = np.array(Image.open("../input/cloudpng/cloud.png"))
            stopwords = set(STOPWORDS)
            wc_neutral = WordCloud(background_color="black",
            colormap='Blues',
            width = 300, height = 200,
            max_words=50,
            stopwords=stopwords,
            repeat=True)
            wc_neutral.generate(str(text))
            wc_neutral.to_file("wc_neutral.png")
            # st.write("Word Cloud Neutral")
            path="wc_neutral.png"
            # st.image(path)
        create_wordcloud_neutral(df_fix_neutral["text_preprocessed"].values)

        #Function to Create Wordcloud
        def create_wordcloud_positive(text):
            #mask = np.array(Image.open("../input/cloudpng/cloud.png"))
            stopwords = set(STOPWORDS)
            wc_positif = WordCloud(background_color="black",
            colormap='Greens',
            width = 300, height = 200,
            max_words=50,
            stopwords=stopwords,
            repeat=True)
            wc_positif.generate(str(text))
            wc_positif.to_file("wc_positif.png")
            # st.write("Word Cloud Positive")
            path="wc_positif.png"
            # st.image(path)
        create_wordcloud_positive(df_fix_positive["text_preprocessed"].values)

        #Function to Create Wordcloud
        def create_wordcloud_negative(text):
            #mask = np.array(Image.open("../input/cloudpng/cloud.png"))
            stopwords = set(STOPWORDS)
            wc_negatif = WordCloud(background_color="black",
            colormap='Reds',
            width = 300, height = 200,
            max_words=50,
            stopwords=stopwords,
            repeat=True)
            wc_negatif.generate(str(text))
            wc_negatif.to_file("wc_negatif.png")
            # st.write("Word Cloud Negative")
            path="wc_negatif.png"
            # st.image(path)
            # display(Image.open(path))
        create_wordcloud_negative(df_fix_negative["text_preprocessed"].values)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.header("Neutral")
            st.image("wc_neutral.png")
            st.dataframe(df_fix_neutral)

        with col2:
            st.header("Positif")
            st.image("wc_positif.png")
            st.write(df_fix_positive[['text','sentimen_score']].sort_values('sentimen_score',ascending=False))
        with col3:
            st.header("Negatif")
            st.image("wc_negatif.png")
            st.write(df_fix_negative[['text','sentimen_score']].sort_values('sentimen_score',ascending=True))
        
        



