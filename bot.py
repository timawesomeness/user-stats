import praw, config, re, time
from datetime import datetime

def main():
    reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent=config.user_agent, username=config.username, password=config.password)

    subreddit = reddit.subreddit("user_stats") # For testing. Will be replaced with checking for mentions to significantly reduce load instead of following /r/all.

    for comment in subreddit.stream.comments():
        if comment.body.find("u/user-stats") != -1: # Temporary as above
            try:
                username = extract_user(comment.body)
            except Exception:
                print(f"Failed on \"{comment.body}\"")
                pass # TODO: save id
            else:
                comment_id, success = reply_stats(comment, username)
                if comment_id and success:
                    pass # TODO: save id

def extract_user(comment):
    username = re.match(r"(/?(u/){1})?\b[\w-]{3,20}\b", comment.lower().split("u/user-stats ")[1])
    if username:
        username = re.sub(r"/?(u/){1}", "", username.group(0))
    else:
        raise Exception
    print(username)
    return username

def reply_stats(comment, username):
    user = reddit.redditor(username)
    posts = user.comments.new(limit=None)
    comments = user.submissions.new(limit=None)
    try:
        stats = compile_stats(posts, comments)
    except (praw.exceptions.PRAWException, prawcore.PrawcoreException) as e:
        print("Bot encountered an error, waiting 5 sec and retrying...\nError: " + str(e))
        try:
            time.sleep(5)
            stats = compile_stats(posts, comments)
        except (praw.exceptions.PRAWException, prawcore.PrawcoreException):
            print(f"Error getting posts/comments for \"{username}\"")
            return None, False
     

def compile_stats(posts, comments):
    # Post vars:
    oldest_post = None
    count_posts = 0
    score_posts = 0
    # Comment vars:
    oldest_comment = None
    count_comments = 0
    score_comments = 0

    for post in posts:
        if oldest_post:
            if post.created < oldest_post:
                oldest_post = post.created
        else:
            oldest_post = post.created
        count_posts += 1
        score_posts += post.score

    for comment in comments:
        if oldest_comment:
            if comment.created < oldest_comment:
                oldest_comment = comment.created
        else:
            oldest_comment = comment.created
        count_comments += 1
        score_posts += 1
    
    if count_comments == 0 and count_posts == 0:
        return "Error. User appears to have 0 posts and 0 comments."

    current_time = datetime.now().timestamp()
    stats_string = (
        f"Stats for *{username}*:\n\n"                                                                                              # For readability's sake:
        f"Over the last **{str(count_posts)}** posts (over {str(round((current_time - oldest_post) / 86400))} days):  \n"           # Post header
        f"Total post score: {str(score_posts)}  \n"                                                                                 #  -Post score
        f"Average post score: {str(round(score_posts / count_posts))}  \n"                                                          #  -Avg. post score
        f"Average post upvotes/day: {str(round(score_posts / ((current_time - oldest_post) / 86400)))}  \n"                         #  -Post score/day
        f"Average posts/day: {str(round(count_posts / ((current_time - oldest_post) / 86400), 3))}\n\n"                             #  -Posts/day
        f"Over the last **{str(count_comments)}* comments (over {str(round((current_time - oldest_comment) / 86400))} days):  \n"   # Comment header
        f"Total comment score: {str(score_comments)}  \n"                                                                           #  -Comment score
        f"Average comment score: {str(round(score_comments / count_comments))}  \n"                                                 #  -Avg. comment score
        f"Average comment upvotes/day: {str(round(score_comments / ((current_time - oldest_comment) / 86400)))}  \n"                #  -Comment score/day
        f"Average comments/day: {str(round(count_comments / ((current_time - oldest_comment) / 86400), 3))}"                        #  -Comments/day
    )
    print(stats_string)
    return stats_string

if __name__ == "__main__":
    main()
