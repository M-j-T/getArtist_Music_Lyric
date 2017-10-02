#!/usr/bin/env python
# -*- coding: utf-8 -*-
# getMoodFromLyrics.py
# by tajima feat.nino
# アーティスト名、そのアーティストの全曲と歌詞情報まで取得してcsvファイルとして出力するコード
from bs4 import BeautifulSoup #スクレイピング用のライブラリ
import urllib.parse
from urllib.parse import urlparse
import urllib.request
from urllib.request import Request, urlopen # 同上
import sys #terminalのコマンドとかが使えるようになるライブラリ
import re #正規表現ライブラリ
import pandas as pd
import csv
#めかぶを使う
import MeCab as mc
from collections import Counter

#csvに出力する配列を宣言
header = ['artist', 'music','categoly'] #ここに出現した単語を追加していく
body=[] #アーティスト名,曲名,カテゴリー,単語の出現回数を記録

#全アーティスト名を取得
def artistName():
	i = 0
	while i<70:
		url = "http://www.uta-net.com/name_list/"+str(i)+"/"

		# FireFoxでアクセスする
		req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
		response = urlopen(req)
		html = response.read()
		soup = BeautifulSoup(html, "lxml")

		# {曲名:歌詞が載っているURL}の辞書song_dictを作る
		song_dict =  {}
		for li in soup.find_all("li"):
			try:
				name = li.p.a.get_text()
				getSong(name) #アーティストごとに曲情報を取得する遠隔操作を実行する
				#リストの長さを揃える
				len_musiclist=[]
				for con in body:
					len_musiclist.append(len(con))
					maxlen=len(con)
				for each_len in len_musiclist:
					diffnum=maxlen-each_len
					i3=0
					while i3<diffnum:
						body[i2].append(0)
						i3=i3+1
				#saveInfo()
			except:
					pass
		i = i + 1

#ブラウザを操作してアーティスト名で検索して曲情報を取得する
def getSong(artist):
	print(artist)
	i = 0
	list_name = []
	while i < 100:
		#アーティスト名で検索
		url = "http://utaten.com/artist/lyric/"+artist+"?sort=popular_sort_asc&page="+str(i)
		#日本語URLにアクセスするための処理
		regex = r'[^\x00-\x7F]'
		matchedList = re.findall(regex,url)
		for m in matchedList:
		   url = url.replace(m, urllib.parse.quote_plus(m, encoding="utf-8"))
		# FireFoxでアクセスする
		req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
		response = urlopen(req)
		html = response.read()
		soup = BeautifulSoup(html, "lxml")
		if len(soup.find_all("td")) == 0:
			i=100 #データがなかったら(アーティストの歌詞情報がサイトになければ終了)
		#アーティストの曲情報を取得
		i2=0
		for td in soup.find_all("td"):
			try:
				name = td.p.get_text() #曲名を取得
				name = re.sub(r'\n| ', "", name) #不要な文字を除去
				if (name in list_name)==True:
					if i>1:
						i=100 #重複していたら終了
						break
				else:
					list_name.append(name)
					href=urllib.parse.unquote(td.a.attrs['href'])
					getlyric(artist,name,href)
			except:
				pass
			i2=i2+1
		i = i + 1

#楽曲ごとに歌詞と印象を取得
def getlyric(artist,name,href):
	#曲の歌詞ページにアクセスしてスクレイピング
	url = "http://utaten.com"+href+"#sort=popular_sort_asc"
	#日本語URLにアクセスするための処理
	regex = r'[^\x00-\x7F]'
	matchedList = re.findall(regex,url)
	for m in matchedList:
	   url = url.replace(m, urllib.parse.quote_plus(m, encoding="utf-8"))
	req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	response = urlopen(req)
	html = response.read()
	soup = BeautifulSoup(html, "lxml")

	#歌詞の出現単語を取得
	lyric=str(soup.find(class_='medium')) #歌詞の文字列を取得
	lyric = re.sub(r'<span class="rt">.*?</span>', "", lyric) #不要な文字を除去
	lyric = re.sub(r'<.*?>', "", lyric) #不要な文字を除去
	words = mecab_analysis(lyric) #メカブで歌詞を形態素解析にかける
	counter = Counter(words) # 集計
	#出力
	music_dic={} #楽曲の単語と出現回数を一時的に格納するための辞書
	for word, count in counter.most_common():
		if len(word) > 0:
			music_dic[word] = count #辞書に追加
			#ヘッダーにない単語なら追加
			if not (word in header)==True:
				header.append(word)

	#曲のカテゴリーを取得
	music_info=[artist,name]
	#None(投票なし)なら0、友情なら1、感動なら2、恋愛なら3、元気なら4
	try:
		get_categoly=str(soup.find(class_='mostVoted').get_text())
		if get_categoly=="友情":
			music_info.append(1)
		elif get_categoly=="感動":
			music_info.append(2)
		elif get_categoly=="恋愛":
			music_info.append(3)
		elif get_categoly=="元気":
			music_info.append(4)
	except:
		music_info.append(0)

	print(music_info)
	print(lyric)

	#ダミーの数字入れとくiretoku
	header_len=len(header)
	j=0
	while j<header_len-3:
		music_info.append(0)
		j=j+1
	#music_dicにheaderに登録いる単語があればその番目に対応した場所に出現頻度を更新
	k=0
	for str_head in header:
		if k>2:
			if str_head in music_dic: #headerに登録されているか確認
				music_info[k]=music_dic[str_head] #対応した番目の出現頻度を更新
		k=k+1
	body.append(music_info)


# mecabを用いて単語に分けます。
def mecab_analysis(text):
	t = mc.Tagger("-Ochasen")
	t.parse('')
	node = t.parseToNode(text)
	output = []
	while node:
		if node.surface != "":  # ヘッダとフッタを除外
			word_type = node.feature.split(",")[0]
			if word_type in ["形容詞", "動詞","名詞", "副詞"]:
				if len(node.surface)>2: #デバック用
					if not re.match('[!-/:-@[-`{-~]|[0-9]', node.surface):
						if not re.match('[a-z]', node.surface):
							output.append(node.surface)
		node = node.next
		if node is None:
			break
	return output

# メイン関数
def main():
	g_artistName = artistName()

if __name__ == '__main__':
	main()