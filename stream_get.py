#---Streaming Get-------------
import html
from mastodon import Mastodon, StreamListener
from janome.tokenizer import Tokenizer
import json, os, re, random
import re

dict_file = "test.json"
dic = {}
t = Tokenizer()

if os.path.exists(dict_file):
    dic = json.load(open(dict_file, "r"))


def register_dic(words):
    global dic
    if len(words) == 0:
        return
    tmp = ["!"]
    for token in words:
        word = token.surface
        if word == "" or word == "\r\n" or word == "\n":
            continue
        tmp.append(word)
        if len(tmp) < 3:
            continue
        if len(tmp) > 3:
            tmp = tmp[1:]
        set_word3(dic, tmp)
        if word == "。" or word == "？":
            tmp = ["!"]
            continue
    json.dump(dic, open(dict_file, "w", encoding="utf-8"))

def set_word3(dic , s3):
    w1, w2, w3 = s3
    if not w1 in dic:
        dic[w1] = {}
    if not w2 in dic[w1]:
        dic[w1][w2] = {}
    if not w3 in dic[w1][w2]:
        dic[w1][w2][w3] = 0
    dic[w1][w2][w3] += 1

def remove_tag(html):
    return re.sub(r"<[^>]+?>", '', html)

def to_oneline(html):
    return html.replace("<br />", ' ').replace("</p><p>", '  ').replace('\n', '\\n')

def remove_mention(content):
    return content.replace("@", "")

def remove_hashtag(content):
    return content.replace("#", "")

def remove_image(content, status):
    for media in status.media_attachments:
        content = content.replace(media.text_url, "")
    return content


mastodon = Mastodon(
    client_id="my_clientcred_workers.txt",
    access_token="my_usercred_workers.txt",
    api_base_url = "https://mstdn-workers.com"
)

class MyStreamListener(StreamListener):
    def __init__(self):
        super(MyStreamListener, self).__init__()


    def handle_stream(self, response):
        try:
            super().handle_stream(response)
        except:
            raise

    def on_update(self, status):
        content = html.unescape(remove_tag(to_oneline(status['content'])))
        content = remove_mention(content)
        content = remove_hashtag(content)
        content = remove_image(content, status)
        print(content)

        if content[-1] != "。":
            content += "。"

        words = t.tokenize(content)
        register_dic(words)


    def on_delete(self, status_id):
        pass


listener = MyStreamListener()
mastodon.stream_local(listener)
