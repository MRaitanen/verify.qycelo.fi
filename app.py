import os
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, session, request, render_template, flash

# Load environment variables
load_dotenv(".env.local")

# Configure application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.template_folder = "html"

# Login route
@app.route("/")
def index():
    dc_login_url = (
        f"{os.getenv('DISCORD_API_BASE')}/oauth2/authorize?"
        f"client_id={os.getenv('CLIENT_ID')}&"
        f"redirect_uri={os.getenv('REDIRECT_URI')}&"
        "response_type=code&"
        "scope=identify guilds.join"
    )
    return redirect(dc_login_url)

# Callback route
@app.route("/callback")
def callback():
    # Check if code is in the request
    code = request.args.get("code")
    data = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("REDIRECT_URI"),
    }

    # Fetch token from Discord
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(
        f"{os.getenv('DISCORD_API_BASE')}/oauth2/token", data=data, headers=headers
    )

    # Check if response is successful
    if response.status_code != 200:
        flash("Error fetching token from Discord.", "error")
        return redirect(url_for("index"))

    # Store token in session
    response_data = response.json()
    session["token"] = response_data["access_token"]
    return redirect(url_for("verify"))

# Verify route
@app.route("/verify")
def verify():
    # Check if token is in session
    headers = {"Authorization": f"Bearer {session['token']}"}
    response = requests.get(f"{os.getenv('DISCORD_API_BASE')}/users/@me", headers=headers)

    # Check if response is successful
    if response.status_code != 200:
        flash("Error fetching user info.", "error")
        return redirect(url_for("index"))

    # Assign role to user
    user_info = response.json()

    # Check if user is already in the guild
    headers_bot = {"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}
    response = requests.put(
        f"{os.getenv('DISCORD_API_BASE')}/guilds/{os.getenv('DISCORD_GUILD_ID')}/members/{user_info['id']}/roles/{os.getenv('VERIFIED_ROLE_ID')}",
        headers=headers_bot
    )

    # Check if response is successful
    if response.status_code == 204:
        return render_template("verify.html", username=user_info["username"], 
                                GUILD_ID=os.getenv("DISCORD_GUILD_ID"),message="Role assigned successfully.")
    else:
        error_message = response.json().get("message", "Failed to assign role.")
        flash(f"Error: {error_message} (Status code: {response.status_code})", "error")
        return render_template("verify.html", username=user_info["username"], GUILD_ID=os.getenv("DISCORD_GUILD_ID"),  message="Role assignment failed.")

# Run application
if __name__ == "__main__":
    app.run(port=8080, debug=False) 
