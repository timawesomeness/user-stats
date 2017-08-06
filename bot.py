import praw, config, re, time, prawcore, string
from datetime import datetime

def main():
    reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent=config.user_agent, username=config.username, password=config.password) 

    print(f"Logged into reddit as /u/{config.username}")
    
    while True:
        try:
            for comment in reddit.inbox.stream():
                if comment.new:
                    try:
                        username = extract_user(comment.body)
                    except Exception:
                        print(f"Failed on \"{comment.body}\"")
                    else:
                        reply_stats(comment, username, reddit)
                    finally:
                        comment.mark_read()
        except (praw.exceptions.PRAWException, prawcore.PrawcoreException) as e:
            print(f"Error connecting to reddit: {str(e)}")
            time.sleep(20)

def extract_user(comment):
    username = re.match(r"(/?(u/){1})?\b[\w-]{3,20}\b", comment.lower().split(f"u/{config.username} ")[1])
    if username:
        username = re.sub(r"/?(u/){1}", "", username.group(0))
    else:
        raise Exception
    return username

def reply_stats(comment, username, reddit):
    user = reddit.redditor(username)
    posts = user.submissions.new(limit=None)
    comments = user.comments.new(limit=None)

    footer = "\n\n___\n\n^[FAQ](https://www.reddit.com/r/user_stats/wiki/faq) ^[Subreddit](https://reddit.com/r/user_stats)"

    try:
        stats = compile_stats(posts, comments, username)
    except (praw.exceptions.PRAWException, prawcore.PrawcoreException) as e:
        if str(e).find("404") != -1:
            stats = f"Error: user \"{username}\" does not seem to exist."
            print(stats)
        else:
            print("Bot encountered an error, waiting 5 sec and retrying...\n    - Error: " + str(e))
            try:
                time.sleep(5)
                stats = compile_stats(posts, comments, username)
            except (praw.exceptions.PRAWException, prawcore.PrawcoreException):
                print(f"Error getting posts/comments for \"{username}\"")
                return
    try:
        comment.reply(stats + footer)
    except (praw.exceptions.PRAWException, prawcore.PrawcoreException):
        try:
            time.sleep(5)
            comment.reply(stats + footer)
        except (praw.exceptions.PRAWException, prawcore.PrawcoreException):
            print(f"Couldn't reply to {comment.id} in /r/{comment.subreddit}. Banned?")
            return

def compile_stats(posts, comments, username):
    # Post vars:
    oldest_post = None
    count_posts = 0
    score_posts = 0
    words_posts = 0
    # Comment vars:
    oldest_comment = None
    count_comments = 0
    score_comments = 0
    words_comments = 0

    for post in posts:
        if oldest_post:
            if post.created_utc < oldest_post:
                oldest_post = post.created_utc
        else:
            oldest_post = post.created_utc
        count_posts += 1
        score_posts += post.score
        words_posts += len(re.sub('[' + string.punctuation + ']', '', post.title).split())

    for comment in comments:
        if oldest_comment:
            if comment.created_utc < oldest_comment:
                oldest_comment = comment.created_utc
        else:
            oldest_comment = comment.created_utc
        count_comments += 1
        score_comments += comment.score
        words_comments += len(re.sub('[' + string.punctuation + ']', '', comment.body).split())
    
    if count_comments == 0 and count_posts == 0:
        return "Error. User appears to have 0 posts and 0 comments."

    current_time = datetime.now().timestamp()

    if not oldest_post:
        oldest_post = current_time
    elif not oldest_comment:
        oldest_comment = current_time

    stats_string = (
        f"**Stats for {username}:**\n\n"                                                                                                                            # For readability:
        f"**Over the last {str(count_posts)} posts (over {str(round((current_time - oldest_post) / 86400))} days):**  \n"                                           # Post header
        f"Total post upvotes: {str(score_posts - count_posts)}  \n"                                                                                                 #  -Post score
        f"Average post score: {str(round(score_posts / count_posts) if count_posts > 0 else 0)}  \n"                                                                #  -Avg. post score
        f"Average post upvotes/day: {str(round((score_posts - count_posts) / ((current_time - oldest_post) / 86400)) if current_time != oldest_post else 0)}  \n"   #  -Post score/day
        f"Average posts/day: {str(round(count_posts / ((current_time - oldest_post) / 86400), 1) if current_time != oldest_post else 0)}  \n"                       #  -Posts/day
        f"Total words in post titles: {str(words_posts)}  \n"                                                                                                       #  -Title words
        f"Average words per post title: {str(round(words_posts / count_posts) if count_posts > 0 else 0)}\n\n"                                                      #  -Avg. title words
        f"**Over the last {str(count_comments)} comments (over {str(round((current_time - oldest_comment) / 86400))} days):**  \n"                                  # Comment header
        f"Total comment upvotes: {str(score_comments - count_comments)}  \n"                                                                                        #  -Comment score
        f"Average comment score: {str(round(score_comments / count_comments) if count_comments > 0 else 0)}  \n"                                                    #  -Avg. comment score
         "Average comment upvotes/day: "                                                                                                                            #  -Comment score/day
            f"{str(round((score_comments - count_comments) / ((current_time - oldest_comment) / 86400)) if current_time != oldest_comment else 0)}  \n"
        f"Average comments/day: {str(round(count_comments / ((current_time - oldest_comment) / 86400), 1) if current_time != oldest_comment else 0)}  \n"           #  -Comments/day
        f"Total words in comments: {str(words_comments)}  \n"                                                                                                       #  -Comment words
        f"Average words per comment: {str(round(words_comments / count_comments) if count_comments > 0 else 0)}"                                                    #  -Avg. comment words
    ) 
    return stats_string

if __name__ == "__main__":
    main()
