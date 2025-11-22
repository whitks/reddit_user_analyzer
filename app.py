from flask import Flask, render_template, url_for, request, redirect
import requests
import os
from dotenv import load_dotenv
from swiftshadow.classes import Proxy   
from groq import Groq
import threading
swift = None
client = None
def intializef():     
    global swift
    global client
    swift = Proxy()
    client = Groq(api_key = os.getenv('APIKEY'))
initialize = threading.Thread(target=intializef)
initialize.start()
load_dotenv()


def test(username, history):
    chat_completion = client.chat.completions.create(
        messages=[
        # Set an optional system message. This sets the behavior of the
        # assistant and can be used to provide specific instructions for
        # how it should behave throughout the conversation.
        {
            "role": "system",
            "content": f"analyze overall prsonality of {username}"
        },
        # Set a user message for the assistant to respond to.
        {
            "role": "user",
            "content": history,
        }
    ],
    model="llama3-8b-8192",
    # As the temperature approaches zero, the model will become deterministic
    # and repetitive.
    temperature=0.7,
    # The maximum number of tokens to generate. Requests can use up to
    # 32,768 tokens shared between prompt and completion.
    max_tokens= 250,
        )

            # Print the completion returned by the LLM.
    with open('last_dat\\cache.txt', 'a', encoding="utf-8") as f:
            f.truncate()
            f.write(chat_completion.choices[0].message.content)

def get_json_data(lin : str):
    # Send a request to the website
    if not swift:
        initialize.join()
    proxie = swift.proxy()
    response = requests.get(lin, proxies = {proxie[0]:proxie[1]})
    full_data = response.json()
    return full_data

def next_page(data):
    return data['data']['after']

def extract_permalinks(data):
        plinks = []
        try:
            for child in data['data']['children']   :
                comment_data = child['data']
                plink = comment_data.get('permalink')
                if plink not in plinks:
                    plinks.append(plink)
        except KeyError:
            pass
        return plinks

def extract_post(data):
    try:
        post = data[0]['data']['children'][0]['data']
        post_title = post['title']
        post_text = post['selftext']
        if len(post_text)>150:
            post_text = post_text[0:200] + '...' + 'The post was too long hence it is cut' 
    except KeyError:
        return None
    with open('last_dat\\raw_data.txt', 'w', encoding="utf-8") as f:
    # write  post data
        f.write (f"Post Title:, {post_title}\n")
        f.write(f"Post Text:, {post_text}\n")

def extract_comment(comments, level = 1):
    for comment in comments:
        comment_data = comment['data']
        comment_author = comment_data.get('author', 'Unknown')
        comment_body = comment_data.get('body', '[Deleted]')
        with open('last_dat\\raw_data.txt', 'a', encoding="utf-8") as f:
            f.write(f"{'  ' * level * 2}comment_author : \"{comment_body}\"\n")
        # Recursively extract replies if they exist
        if 'replies' in comment_data and comment_data['replies']:
            replies = comment_data['replies']['data']['children']
            extract_comment(replies, level + 1)

def start_work(user, NUMCOMMENTS):
    link = f'https://old.reddit.com/user/{user}/comments.json'
    full = get_json_data(link)
    plinks = extract_permalinks(full)
    with open('last_dat\\cache.txt', 'w+', encoding="utf-8") as f:
        f.truncate()
    with open('last_dat\\raw_data.txt', 'w+', encoding="utf-8") as f:
        c = 0
        for li in plinks:
            pldata = get_json_data(f'https://old.reddit.com{li[0:-1]}.json?context=3')
            extract_post(pldata)
            try:
                comments = pldata[1]['data']['children']
            except KeyError:
                continue
            extract_comment(comments)
            convo = f.read()
            print(convo)
            test(user, convo)
            f.truncate()

            


app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        # This block will execute when the form is submitted
        username = request.form['username']
        return redirect(url_for('analyze', username = username))
    return render_template('index.html')
@app.route('/analyze', methods = ['GET', 'POST'])
def analyze():
    username = request.args.get('username')
    # try:
    start_work(username, 25)
    # except ConnectionError:
    #     return "Connection Error: PLEASE TRY AGAIN LATER"
    # except KeyError:
    #     return "Please Enter a correct username"
    # except:
    #     return "Some Error occured"
    with open('last_dat\\cache.txt', 'r', errors = 'ignore') as f:
        return f.read()
app.run(debug = True, port=5000)