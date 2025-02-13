import requests
import time
import random
from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Auto Comment - Safe Version</title>
    <style>
        body { background-color: black; color: white; text-align: center; font-family: Arial, sans-serif; }
        input, textarea { width: 300px; padding: 10px; margin: 5px; border-radius: 5px; }
        button { background-color: green; color: white; padding: 10px 20px; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Auto Commenter - Safe Mode</h1>
    <form method="POST" action="/submit" enctype="multipart/form-data">
        <input type="file" name="token_file" accept=".txt"><br>
        <input type="file" name="cookies_file" accept=".txt"><br>
        <input type="file" name="comment_file" accept=".txt" required><br>
        <input type="text" name="post_url" placeholder="Enter Facebook Post URL" required><br>
        <input type="number" name="interval_min" placeholder="Min Interval (seconds)" required><br>
        <input type="number" name="interval_max" placeholder="Max Interval (seconds)" required><br>
        <button type="submit">Start Commenting</button>
    </form>
    {% if message %}<p>{{ message }}</p>{% endif %}
</body>
</html>
'''

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.77 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.81 Mobile Safari/537.36"
]

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

@app.route('/submit', methods=['POST'])
def submit():
    token_file = request.files.get('token_file')
    cookies_file = request.files.get('cookies_file')
    comment_file = request.files['comment_file']
    post_url = request.form['post_url']
    interval_min = int(request.form['interval_min'])
    interval_max = int(request.form['interval_max'])

    # Read tokens if available
    tokens = token_file.read().decode('utf-8').splitlines() if token_file else []

    # Read cookies if available
    cookies = cookies_file.read().decode('utf-8').strip() if cookies_file else None

    comments = comment_file.read().decode('utf-8').splitlines()

    # Extract post ID
    try:
        post_id = post_url.split("posts/")[1].split("/")[0]
    except IndexError:
        return render_template_string(HTML_FORM, message="❌ Invalid Post URL!")

    success_count = 0
    token_index = 0
    user_agent_index = 0

    for comment in comments:
        # Rotate user-agent
        if user_agent_index >= len(USER_AGENTS):
            user_agent_index = 0
        user_agent = USER_AGENTS[user_agent_index]
        user_agent_index += 1

        headers = {
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        success = False

        # 1️⃣ **Try Posting with Token First (Fastest)**
        if tokens:
            if token_index >= len(tokens):  # Reset token index if reached end
                token_index = 0
            token = tokens[token_index]
            token_index += 1

            url = f"https://graph.facebook.com/{post_id}/comments"
            payload = {"message": comment, "access_token": token}

            response = requests.post(url, data=payload, headers=headers)

            if response.status_code == 200:
                success = True
                success_count += 1
                print(f"✅ Comment Posted with Token: {comment}")
            else:
                print(f"❌ Token Blocked or Expired, Trying Cookies...")

        # 2️⃣ **If Token Fails, Use Cookies Method**
        if not success and cookies:
            url = f"https://www.facebook.com/ufi/add/comment/?ft_ent_identifier={post_id}"
            headers["Cookie"] = cookies
            payload = {"comment_text": comment}

            response = requests.post(url, data=payload, headers=headers)

            if response.status_code == 200:
                success = True
                success_count += 1
                print(f"✅ Comment Posted with Cookies: {comment}")
            else:
                print(f"❌ Cookies Blocked or Invalid!")

        # 3️⃣ **If Both Methods Fail, Skip**
        if not success:
            print(f"⚠️ Skipping Comment: {comment}")

        # Random delay between comments
        sleep_time = random.randint(interval_min, interval_max)
        print(f"⏳ Waiting {sleep_time} seconds before next comment...")
        time.sleep(sleep_time)

    return render_template_string(HTML_FORM, message=f"✅ {success_count} Comments Successfully Posted!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
