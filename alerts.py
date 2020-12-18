import smtplib
from email.message import EmailMessage
import praw
import time
import re
from datetime import datetime

#get time from post
def time_passed(post_timestamp):
    now = datetime.timestamp(datetime.now())
    return (now - post_timestamp)

#function to send email
def alert(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg["subject"] = subject
    msg["to"] = to
    msg["from"] = "email your message will be sent from"

    server = smtplib.SMTP("smtp.gmail.com", 587) #this is assuming gmail, other services will use another port etc.
    server.starttls()
    server.login("email", "password")
    server.send_message(msg)
    server.quit()

#get info from a submission
def sub_info(submission):
    title = str(submission.title)
    author = str(submission.author)
    url = "https://www.reddit.com" + str(submission.permalink)
    data = re.sub("[^a-zA-Z0-9\[\]:;!@#$%^&*()=+.,<>?{}\-/ ]+", "", (title + " " + author + " " + str(submission.created_utc)))
    time_since_post = time_passed(submission.created_utc)
    return {"title":title, "author":author, "url":url, "data":data, "time_since_post":time_since_post}

#logging into reddit api
reddit = praw.Reddit(client_id="client id",
                     client_secret="reddit client secret",
                     user_agent="abritrary name")

#run until interrupted
users = [
            {
                "address":"email to send to", #to send to a phone, tmobile: 2222222222@tmomail.net, verizon: 2222222222@vtext.com
                "known":[],
                "alert":3, #three levels of alerts which can be easily customized
                "subreddits":[
                                {
                                    "subreddit":"subreddit name (one word)",
                                    "exclusions":["word"],
                                    "blacklist":["user1", "user2", "user3"]
                                },
                                {
                                    "subreddit":"subreddit2",
                                    "exclusions":[],
                                    "blacklist":["user4", "user5", "user6"]
                                }
                             ]
            }, #you can add another address to send messages to after this
            {
                "address":"email to send to", #to send to a phone, tmobile: 2222222222@tmomail.net, verizon: 2222222222@vtext.com
                "known":[],
                "alert":3, #three levels of alerts which can be easily customized
                "subreddits":[
                                {
                                    "subreddit":"subreddit name (one word)",
                                    "exclusions":["word"],
                                    "blacklist":["user1", "user2", "user3"]
                                },
                                {
                                    "subreddit":"subreddit2",
                                    "exclusions":[],
                                    "blacklist":["user4", "user5", "user6"]
                                }
                             ]
            }
        ]

checks = 0
while True:
    prev_length = len(users[0]["known"])
    temp_sub_data = {}
    #for each user in dictionary
    for user in users:
        #going through each subreddit listed
        for subreddit in user["subreddits"]:
            #get data if not already retrieved
            if subreddit["subreddit"] not in temp_sub_data.values():
                temp_sub_data[subreddit["subreddit"]] = reddit.subreddit(subreddit["subreddit"]).new(limit=5) #default of 5
            #now that we have 5 most recent posts, cycle through them
            for submission in temp_sub_data[subreddit["subreddit"]]:
                info = sub_info(submission)
                #if new, less than 5 minutes old, and not in database, add to database
                if (info["data"] not in user["known"]) and (info["time_since_post"] < 300):#default of 300
                    #add to database
                    user["known"].append(info["data"])
                    #making sure not from blacklisted user
                    if info["author"].lower() not in subreddit["blacklist"]:
                        #making sure title contains no exclusions
                        if not any(n in info["title"].lower() for n in subreddit["exclusions"]):
                            print("Sending alert to " + user["address"] + ": " + "(" + info["author"] + ") " + info["title"] + " " + info["url"])
                            #send alert based off of what type of alert user wants
                            if user["alert"] == 1:
                                alert(info["title"], info["url"], user["address"])
                                time.sleep(3)
                            elif user["alert"] == 2:
                                alert(info["author"], info["title"], user["address"])
                                time.sleep(3)
                                alert("", info["url"], user["address"])
                                time.sleep(3)
                            elif user["alert"] == 3:
                                alert(info["author"], info["title"], user["address"])
                                time.sleep(3)

    #every 100 checks notify bot is still working
    checks += 1
    if checks%500 == 0:
        alert("Bot still on", ("checks: " + str(checks)), "email")
    #if no length change then there were no new posts
    if prev_length == len(users[0]["known"]):
        print('No new posts')
        #wait 30 seconds before checking again
        time.sleep(30)
    else:
        #since there was at least 20 second delay
        time.sleep(10)
