#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen, Request
from urllib.parse import quote
import sys, os, subprocess, re

from threading import Thread
from queue import Queue
import time

loaded = False
said = False

q_mp3 = Queue()

say = True
compress = False
lang = 'ru'

def loader(parts):

	global loaded

	if compress:
		file_parts = []

	for i, part in enumerate(parts):

		part = part.replace('\n', '')
		part = part.strip()

		if not part:
			continue

		print('http://translate.google.com/translate_tts?tl={}'.format(lang))

		request = Request('http://translate.google.com/translate_tts?tl={}'.format(lang), data='q={}'.format(quote(part)).encode())
		request.add_header('Host', 'translate.google.com')
		request.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0')
		request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
		request.add_header('Accept-Language', 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3')

		try:
			data = urlopen(request)
			mp3 = data.read()
		except Exception as e:
			print('error: {}'.format(e))
			continue

		q_mp3.put(mp3)

		if compress:
			try:
				os.mkdir('tmp')
			except:
				pass
			with open('tmp/{}.mp3'.format(i), 'wb') as f:
				f.write(mp3)
			file_parts.append('tmp/{}.mp3'.format(i))

	loaded = True
	if compress:

		cmd = '{}ffmpeg -i "concat:{}" tmp/{}.mp3'.format('./' if os.path.exists('ffmpeg') else '', '|'.join(file_parts), time.strftime('%Y.%m.%d_%H-%M-%S'))
		p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		print(p.stdout.read().decode())
		for f in file_parts:
			try:
				os.unlink(f)
			except:
				pass

def sound():

	global said

	p = subprocess.Popen('mpg123 -', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	while True:

		if loaded is True and q_mp3.empty():
			break

		if q_mp3.empty():
			time.sleep(.1)
			continue

		mp3 = q_mp3.get(True, 1)
		
		try:
			p.stdin.write(mp3)
		except:
			print("can't find mpg123\ninstall it\n")
			return

	time.sleep(2)

	p.communicate()[0]
	p.stdin.close()

	said = True

def main():

	global say
	global compress
	global lang

	if len(sys.argv) < 2:
		print("USAGE: {} text or file name [-cslh]".format(sys.argv[0]))
		exit()

	if len(sys.argv) > 2:
		for i, arg in enumerate(sys.argv[2:]):
			if not arg.startswith('-'):
				continue

			if 'c' in arg:
				compress = True
				say = False
			if 's' in arg:
				say = True
			if 'l' in arg:
				try:
					lang = sys.argv[i+3].strip()
				except:
					print('language is not set')
					return
	text = sys.argv[1]
	if text == '-h':
		print('\narguments:\n-c compress all data to mp3 file. Talking will be disabled\n-s enable talking.\n-l change language\n-h show this help\n')
		return
	if os.path.exists(text):
		with open(text, 'r') as f:
			text = f.read()

	text += ' '

	if len(text) > 100:

		parts = re.findall('.{,98}\s', text)
	else:
		parts = [text]

	t1 = Thread(target=loader, args=(parts,))
	t1.start()

	if say:
		t2 = Thread(target=sound)
		t2.start()

	try:
		t1.join()
		if say:
			t2.join()
	except:
		pass
	
if __name__ == '__main__':
	main()

