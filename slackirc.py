import setting
import requests, json, asyncio, websockets, socket, ssl, threading

async def main():
	ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
	ctx.verify_mode = ssl.CERT_NONE
	reader, writer = await asyncio.open_connection(setting.SERVER[0], setting.SERVER[1], ssl = ctx)
	writer.write(b'USER slackbot hostname servername :realname\r\n')
	writer.write(b'NICK %s\r\n' % setting.NICK.encode('utf-8'))
	await writer.drain()
	while True:
		msg = await reader.readline()
		if msg.find(b'Welcome') != -1:
			writer.write(b'JOIN #%s\r\n' % setting.IRC_CHANNEL.encode('utf-8'))
			await writer.drain()
			break
	s = requests.session()
	c = dict()
	d = dict()
	msg = json.loads(s.get('https://slack.com/api/rtm.start?token=' + setting.TOKEN).text)
	for r in msg['users']:
		c[r['name']] = r['id']
		d[r['id']] = r['name']
	r = {'token': setting.TOKEN, 'channel': setting.SLACK_CHANNEL, 'as_user': False}
	async with websockets.connect(msg['url']) as slack:
		i = 0
		while True:
			__slack = asyncio.ensure_future(slack.recv())
			__irc = asyncio.ensure_future(reader.readline())
			done, pending = await asyncio.wait([__slack, __irc], return_when = asyncio.FIRST_COMPLETED)

			if __slack in done:
				msg = json.loads(__slack.result())
				if 'type' in msg and msg['type'] == 'message' and 'channel' in msg and msg['channel'] == setting.SLACK_CHANNEL and 'text' in msg and 'user' in msg:
					tmp = msg['text']
					for x in d:
						tmp = tmp.replace('<@' + x + '>', '<@' + d[x] + '>')
					tmp = tmp.replace('&lt;', '<').replace('&gt;', '>')
					for x in tmp.splitlines():
						if msg['user'] not in d:
							tmp = json.loads(s.get('https://slack.com/api/rtm.start?token=' + setting.TOKEN).text)
							for tt in tmp['users']:
								c[tt['name']] = tt['id']
								d[tt['id']] = tt['name']
						x = '<' + d[msg['user']] + '> ' + x
						writer.write(b'PRIVMSG #%s :%s\r\n' % (setting.IRC_CHANNEL.encode('utf-8'), x.encode('utf-8')))
						await writer.drain()
						print('--> | ' + x)
			else:
				__slack.cancel()

			if __irc in done:
				try:
					msg = __irc.result()[:-2].decode('utf-8')
					if msg[:5] == 'PING ':
						writer.write(b'PONG ' + msg[5:].encode('utf-8') + b'\r\n')
						await writer.drain()
					else:
						j = msg.find(' PRIVMSG #%s :' % setting.IRC_CHANNEL)
						if j != -1:
							i += 1
							tmp = msg[j+17:]
							for x in c:
								tmp = tmp.replace('<@' + x + '>', '<@' + c[x] + '>')
							r['text'] = tmp
							r['username'] = msg[1:msg.find('!')]
							s.post('https://slack.com/api/chat.postMessage', data = r)
							print('<-- | <' + r['username'] + '> ' + r['text'])
				except:
					pass
			else:
				__irc.cancel()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
