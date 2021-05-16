import re
import requests
import pandas as pd
from urllib import parse
from bs4 import BeautifulSoup

headers = {  # 构造请求头部
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  + "AppleWebKit/537.36 (KHTML, like Gecko) "
                  + "Chrome/89.0.4389.128 Safari/537.36"
}


def sub_analyze(sub_response):
    sub_soup = BeautifulSoup(sub_response, 'html.parser')
    info = sub_soup.findAll("div", id="info")
    info = info[0]
    string = info.text
    string = re.sub(r':\n +', ': ', string)
    string = re.sub(r'\n +', '', string)
    string = re.sub(r'\n+', '\n', string)
    string = re.sub(r'\n', '', string, 1)  # 使用正则表达式处理，去除多余的空格和换行
    string = string.replace(u'\xa0', u' ')
    result = string.split('\n')[0:-1]
    return result


def analyze(response, cookies):
    results = []
    soup = BeautifulSoup(response, 'html.parser')
    books = soup.findAll("div", class_="pl2")
    for book in books:
        result = []
        title = book.a['title']
        result.append(title)
        sub_url = book.a['href']
        sub_response = requests.get(sub_url, headers=headers, cookies=cookies)  # 内层爬取
        print(sub_response)
        sub_result = sub_analyze(sub_response.content.decode('utf-8'))  # 解析爬取到的信息
        result.append(sub_result)
        results.append(result)
    return results


def login():
    name = input('输入手机号码：')
    password = input('输入密码：')
    url = 'https://accounts.douban.com/j/mobile/login/basic'
    # parameters required for login
    data = {
        'ck': '',
        'name': name,
        'password': password,
        'remember': '',
        'ticket': ''
    }
    data = parse.urlencode(data)
    response = requests.post(url, headers=headers, data=data, verify=False)
    return requests.utils.dict_from_cookiejar(response.cookies)  # 返回登录的cookies


def main():
    flag = input('输入1登录爬取，输入其他内容不登陆爬取：')
    if flag == '1':
        cookies = login()
    else:
        cookies = None
    df = pd.DataFrame(columns=['书名'])
    url = "https://book.douban.com/top250"
    for i in range(3):  # 为防止被反爬机制阻挡，仅爬取前3页
        response = requests.get(url + "?start=" + str(i * 25), headers=headers, cookies=cookies)  # 外层爬取
        print(response)
        results = analyze(response.content.decode('utf-8'), cookies)  # 解析爬取到的信息
        for book in results:
            df = df.append({'书名': book[0]}, ignore_index=True)
            for attribute in book[1]:
                li = attribute.split(': ')
                if li[0] not in list(df):  # 每本书拥有的属性可能不同，对于未出现过的属性建立新列
                    df.insert(len(list(df)), li[0], '')
                df.loc[len(df)-1, li[0]] = li[1]
    df.to_csv("result.csv", encoding='utf-8_sig')


if __name__ == '__main__':
    main()
