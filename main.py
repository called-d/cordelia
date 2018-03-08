#coding: utf-8

import html
from janome.tokenizer import Tokenizer
import json, os, re, random
import re
from mastodon import Mastodon, StreamListener

censorship_command = re.compile(r'^コーデリア\s禁止用語')

#学習辞書
dict_file = "dict.json"
dic = {}
t = Tokenizer()

#禁止用語辞書
censor_file = "censor_data.json"
censor_dic = {}

admin_user_id = '2028'


#-----文章生成関数群----------------------------------------------------

def analisys(text):
    malist = t.tokenize(text)
    return malist

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

def make_sentence(head):
    if not head in dic:
        return ""
    ret = []
    if head != "!":
        ret.append(head)
    top = dic[head]
    w1 = word_choice(top)
    w2 = word_choice(top[w1])
    ret.append(w1)
    ret.append(w2)
    while True:
        if w1 in dic and w2 in dic[w1]:
            w3 = word_choice(dic[w1][w2])
        else:
            w3 = ""
        ret.append(w3)
        if w3 == "。" or w3 == "？" or w3 == "":
            break
        w1, w2 = w2, w3
    return "".join(ret)

def word_choice(sel):
    keys = sel.keys()
    return random.choice(list(keys))

def make_reply(text):
    if text[-1] != "。":
        text += "。"
    words = t.tokenize(text)
    #register_dic(words)

    for w in words:
        face = w.surface
        ps = w.part_of_speech.split(',')[0]
        if ps == "感動詞":
            return face + "。"
        if ps == "名詞" or ps == "形容詞":
            if face in dic:
                return make_sentence(face)
    return make_sentence("!")


#-----リプライ処理------------------------------------------------------------

def remove_tag(html):
    return re.sub(r"<[^>]+?>", '', html)

def to_oneline(html):
    return html.replace("<br />", ' ').replace("</p><p>", '  ').replace('\n', '\\n')

def remove_mention(content):
    text = re.split(" +", content, maxsplit=1)
    return text[1]

def remove_hashtag(content):
    return content.replace("#", "")

def remove_image(content, status):
    for media in status.media_attachments:
        content = content.replace(media.text_url, "")
    return content

def content_to(status):
    content = html.unescape(remove_tag(to_oneline(status['content'])))
    content = remove_mention(content)
    content = remove_hashtag(content)
    content = remove_image(content, status)


#-----リプライ関数群---------------------------------------------------------

def listen_func_check(status):
    if os.path.exists(censor_file):
        censor_dic = json.load(open(censor_file, "r"))

    content = content_to(status)
    censor_text = re.sub(r'[.*コーデリア\s禁止用語.*]', '', content)
    if(censor_text):
        censor_dic['censorships'].append(censor_text)
        json.dump(censor_dic, open(censor_file, "w", encoding="utf-8"))
        mastodon.toot('禁止用語に設定しました')

#フィルタ　引っかかればTrue
def my_fair_lady(reply, dic):
    censor_list = dic['censorships']
    match_obj = -1
    for text in censor_list:
        match_obj = reply.find(text)
        if(match_obj):
            break

    if(match_obj == -1):
        return False
    else:
        return True

def default_analisys(status):
    reply = 0
    censor_dic = json.load(open(censor_file, "r"))
    #リプライ文を取得
    reply_text = str(content_to(status))

    #禁止用語の設定
    if censorship_command.match(reply_text):
        if(status['account']['id'] == admin_user_id):
            listen_func_check(status)
        else:
            mastodon.toot('権限がありません')

    #リプライ文の生成
    reply = make_reply(reply_text)
    print(reply)
    censorship = my_fair_lady(reply, censor_dic)

    if(censorship):
        mastodon.toot('変なこと言わせないでくれる?')
    else:
        mastodon.toot(reply)


#-----Streaming処理,mention取得------------------------------------------------

class MyStreamListener(StreamListener):
    def __init__(self):
        super(MyStreamListener, self).__init__()

    def handle_stream(self, response):
        try:
            super().handle_stream(response)
        except:
            raise

    def on_update(self, status):
        pass

    def on_delete(self, status_id):
        pass

    def on_notification(self, notification):
        if notification['type'] == 'mention':
            default_analisys(notification['status'])


if __name__ == "__main__":
    if os.path.exists(dict_file):
        dic = json.load(open(dict_file, "r"))

    mastodon = Mastodon(
        client_id="my_clientcred_workers.txt",
        access_token="my_usercred_workers.txt",
        api_base_url = "https://mstdn-workers.com"
    )

    listener = MyStreamListener()
    mastodon.stream_user(listener)
