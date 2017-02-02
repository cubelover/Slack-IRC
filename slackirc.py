import settings
import requests
import json
import asyncio
import websockets
import ssl
import threading


@asyncio.coroutine
def main():
	ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
	ctx.verify_mode = ssl.CERT_NONE
	reader, writer = yield from asyncio.open_connection(settings.SERVER[0], settings.SERVER[1], ssl = ctx)
	writer.write(b'USER slackbot hostname servername :realname\r\n')
	writer.write(b'NICK %s\r\n' % settings.NICK.encode('utf-8'))
	yield from writer.drain()
	while True:
		msg = yield from reader.readline()
		if msg.find(b'Welcome') != -1:
			writer.write(b'JOIN #%s\r\n' % settings.IRC_CHANNEL.encode('utf-8'))
			yield from writer.drain()
			break

	s = requests.session()
	c = dict()
	d = dict()

	msg = json.loads(s.get('https://slack.com/api/rtm.start?token=' + settings.TOKEN).text)
	SLACK_CHANNEL_ID = list(filter(lambda c: c['name'] == settings.SLACK_CHANNEL, msg['channels']))[0]['id']
	for r in msg['users']:
		c[r['name']] = r['id']
		d[r['id']] = r['name']
	r = {'token': settings.TOKEN, 'channel': settings.SLACK_CHANNEL, 'as_user': False}
	slack = yield from websockets.connect(msg['url'])
	i = 0

	while True:
		__slack = asyncio.ensure_future(slack.recv())
		__irc = asyncio.ensure_future(reader.readline())
		done, pending = yield from asyncio.wait([__slack, __irc], return_when = asyncio.FIRST_COMPLETED)

		if __slack in done:
			msg = json.loads(__slack.result())
			if 'type' in msg and msg['type'] == 'message' and 'subtype' not in msg and msg['channel'] == SLACK_CHANNEL_ID:
				tmp = msg['text']
				for x in d:
					tmp = tmp.replace('<@' + x + '>', '<@' + d[x] + '>')
				tmp = tmp.replace('&lt;', '<').replace('&gt;', '>')
				for x in tmp.splitlines():
					if msg['user'] not in d:
						tmp = json.loads(s.get('https://slack.com/api/rtm.start?token=' + settings.TOKEN).text)
						for tt in tmp['users']:
							c[tt['name']] = tt['id']
							d[tt['id']] = tt['name']
					x = '<' + d[msg['user']] + '> ' + x
					writer.write(b'PRIVMSG #%s :%s\r\n' % (settings.IRC_CHANNEL.encode('utf-8'), x.encode('utf-8')))
					yield from writer.drain()
					print('--> | ' + x)
		else:
			__slack.cancel()

		if __irc in done:
			try:
				msg = __irc.result()[:-2].decode('utf-8')
				print(msg)
				if msg[:5] == 'PING ':
					writer.write(b'PONG ' + msg[5:].encode('utf-8') + b'\r\n')
					yield from writer.drain()
				else:
					j = msg.find(' PRIVMSG #%s :' % settings.IRC_CHANNEL)
					prelen = len(' PRIVMSG #%s :' % settings.IRC_CHANNEL)
					if j != -1:
						i += 1
						tmp = msg[j+prelen:]
						for x in c:
							tmp = tmp.replace('<@' + x + '>', '<@' + c[x] + '>')
						r['text'] = tmp
						r['username'] = msg[1:msg.find('!')]
						s.post('https://slack.com/api/chat.postMessage', data = r)
						print('<-- | <' + r['username'] + '> ' + r['text'])
			except Exception as e:
				print(e)
				pass
		else:
			__irc.cancel()


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
	loop.close()
