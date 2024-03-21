# Getting Started

## Creating the Reddit app

In your browser, when you are logged in with the Reddit account you want to use, go to this URL: https://www.reddit.com/prefs/apps

Once there, click the “are you a developer? create an app...” button at the bottom. Name the app anything you want. Then **CLICK THE SCRIPT OPTION**, this is important.

You can leave the description and about URL empty, but you need to put a value for the redirect URI. This can be anything as long as it is a valid URL. I recommend putting `http://127.0.0.1`.

Then click Create App.

You will find your client id and secret. Now we are ready to get the bot up and running!

Open `reddit_ai_moderation.py` using a text editor and input these credentials. You can input `AI Modbot 0.1` for `user_agent`. Input your reddit bot account's username and password. Finally, edit the subreddit name to monitor.

#### Configure what actions the Reddit bot performs

The default probability value is 0.7/1.0. It can be set separately for the original comment and translated comment. Decreasing these values will increase the probability of false positives and the chance the removal action is performed. The default values are fine, but you can experiment.

#### System requirements for running the bot

For Linux OS, a swap space of at least 3 GB is required for systems with 1 GB of RAM. A swap space of 2 GB is required for systems with 2 GB of RAM.
