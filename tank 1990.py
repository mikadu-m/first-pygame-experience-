import pygame
import random
import pika
import uuid
import json
from threading import Thread
import math
import numpy as np


pygame.init()

screen = pygame.display.set_mode((800, 600))

def multi():
	IP = '34.254.177.17'
	PORT = 5672
	virthost = 'dar-tanks' 
	usname = 'dar-tanks'
	passw = '5orPLExUYnyVYZg48caMpX'


	pygame.init()
	screen = pygame.display.set_mode((1100, 600))
	font = pygame.font.Font('Wandery_Bold.ttf', 17)
	ss2 = pygame.mixer.Sound("sss.wav")
	# pygame.mixer.music.load("back.mp3")
	# pygame.mixer.music.play(-1)




	class TankRPC:
		def __init__(self):
			self.connection = pika.BlockingConnection( 
				pika.ConnectionParameters(
					host = IP, 
					port = PORT, 
					virtual_host = virthost,
					credentials = pika.PlainCredentials(
						username = usname,
						password = passw)))
			self.channel = self.connection.channel()
			queue = self.channel.queue_declare(queue = '',
												auto_delete = True,
												exclusive = True)
			self.callback_queue = queue.method.queue
			self.channel.queue_bind(
				exchange = 'X:routing.topic',
				queue = self.callback_queue
				)
			self.channel.basic_consume(
				queue = self.callback_queue,
				on_message_callback = self.on_response,
				auto_ack = True)
			
			self.response = None
			self.corr_id = None
			self.token = None
			self.tank_id = None
			self.room_id = None


		def on_response(self, ch, method, props, body):
			if self.corr_id == props.correlation_id:
				self.response = json.loads(body)
				print(self.response)
			

		def call(self, key, message={}):
			self.response = None
			self.corr_id = str(uuid.uuid4())
			
			self.channel.basic_publish(
				exchange = 'X:routing.topic',
				routing_key = key,
				properties = pika.BasicProperties(
					reply_to = self.callback_queue,
					correlation_id = self.corr_id,
					),
				body = json.dumps(message))
			while self.response is None:
				self.connection.process_data_events()
				

		def check_server_status(self):
			self.call('tank.request.healthcheck')
			return self.response['status'] == '200'


		def register(self, room_id):
			message = {
			'roomId' : room_id
			}
			self.call('tank.request.register', message)
			if 'token' in self.response:
				self.token = self.response['token']
				self.tank_id = self.response['tankId']
				self.room_id = self.response['roomId']
				return True
			return False
				

		def turn_tank(self, token, direction):
			message = {
				'token' : token,
				'direction' : direction 
			}
			self.call('tank.request.turn', message)


		def fire_bullet(self, token):
			message = {
			'token': token
			}

			self.call('tank.request.fire', message)

			# if self.response['message'] == "You are firing too fast. A Tank can fire once per second.":
			# 	pygame.mixer.Sound.play(ss2)
				



	class Player_consumer(Thread):
		def __init__(self, room_id):
			super().__init__()
			self.connection = pika.BlockingConnection( 
				pika.ConnectionParameters(
					host = IP, 
					port = PORT, 
					virtual_host = virthost,
					credentials = pika.PlainCredentials(
						username = usname,
						password = passw)))
			self.channel = self.connection.channel()
			queue = self.channel.queue_declare(queue = '',
												auto_delete = True,
												exclusive = True)
			event_listener = queue.method.queue
			self.channel.queue_bind(exchange = 'X:routing.topic',
									queue = event_listener,
									routing_key = 'event.state.' + room_id)
			self.channel.basic_consume(
				queue = event_listener,
				on_message_callback = self.on_response, 
				auto_ack = True)
			self.response = None

		def on_response(self, ch, method, props, body):
			self.response = json.loads(body)
			print(self.response)

		def run(self):
			self.channel.start_consuming()



	UP = 'UP'
	DOWN = 'DOWN'
	LEFT = 'LEFT'
	RIGHT = 'RIGHT'

	MOVE_KEYS = {
		pygame.K_UP: UP,
		pygame.K_DOWN: DOWN,
		pygame.K_LEFT: LEFT,
		pygame.K_RIGHT: RIGHT
	}

	def background():
		back = pygame.image.load("background.png")
		back = pygame.transform.scale(back, (830, 600))
		screen.blit(back, (0, 0))

	def panel():
		border = pygame.image.load("border.png")
		border = pygame.transform.scale(border, (260, 600))
		screen.blit(border, (830, 0))
		ii = 0
		tank_list = []
		data_type = [('tank_id', int),('score', int), ('health', int)]
		for tank in player.response['gameField']['tanks']:
			temp = (int(tank['id'][5:]),tank['score'],tank['health'])
			tank_list.append(temp)
		tank_list_np = np.array(tank_list, dtype = data_type)
		tl_sorted = np.sort(tank_list_np, order =  ['score', 'health'])[::-1]

		for i in range(len(tl_sorted)):
			text_score = font.render("ID: {0}|  SCORE: {1} | HEALTH:  {2}".format(
				tl_sorted[i][0],
				tl_sorted[i][1],
				tl_sorted[i][2]),
				True, 
				(211, 211, 255))
			screen.blit(text_score, (840, ii + 180))
			ii += 25	


	def draw_bullet(x, y, width, height, direction, owner):
		bullet_im = pygame.image.load("bullet11.png")
		bullet_im2 = pygame.image.load("bullet22.png")
		bullet_im = pygame.transform.scale(bullet_im, (5, 15))
		bullet_im2 = pygame.transform.scale(bullet_im2, (5, 15))
		bullet_trans = bullet_im
		bullet_trans2 = bullet_im2
		if owner == user.tank_id:
			if direction == 'UP':
				bullet_im = bullet_trans
			if direction == 'LEFT':
				bullet_im = pygame.transform.rotate(bullet_trans, 90)
			if direction == 'RIGHT':
				bullet_im = pygame.transform.rotate(bullet_trans, -90)
			if direction == 'DOWN':
				bullet_im = pygame.transform.rotate(bullet_trans, 180)	
			screen.blit(bullet_im, (x, y))
		else:
			if direction == 'UP':
				bullet_im2 = bullet_trans2
			if direction == 'LEFT':
				bullet_im2 = pygame.transform.rotate(bullet_trans2, 90)
			if direction == 'RIGHT':
				bullet_im2 = pygame.transform.rotate(bullet_trans2, -90)
			if direction == 'DOWN':
				bullet_im2 = pygame.transform.rotate(bullet_trans2, 180) 
			screen.blit(bullet_im2, (x, y))

	def draw_tank(x, y, width, height, direction, score, health, id):
		tank_c = (x + int(width/2), y + int(width / 2))
		image_tank = pygame.image.load("tank_con.png")
		image_tank2 = pygame.image.load("tank_con_2.png")
		image_tank = pygame.transform.scale(image_tank, (width, height))
		image_tank2 = pygame.transform.scale(image_tank2, (width, height))
		tank_transform = image_tank
		tank_transform2 = image_tank2

		
		if id == user.tank_id:
			text = font.render("YOUR SCORE:" + str(score), True, (211, 211, 255))
			text2 = font.render("YOUR HEALTH:" + str(health), True, (211, 211, 255))
			text3 = font.render("TIME: " + str(player.response['remainingTime']), True, (211, 211, 255))
			screen.blit(text, (840, 25))
			screen.blit(text2, (840, 50))
			screen.blit(text3, (840, 75))
			if direction == 'UP':
				image_tank = tank_transform
			if direction == 'DOWN':
				image_tank = pygame.transform.rotate(tank_transform, 180)
			if direction == 'LEFT':
				image_tank = pygame.transform.rotate(tank_transform, 90)
			if direction == 'RIGHT':
				image_tank = pygame.transform.rotate(tank_transform, -90)
			screen.blit(image_tank, (x, y))
		else:
			if direction == 'UP':
				image_tank2 = tank_transform2
			if direction == 'DOWN':
				image_tank2 = pygame.transform.rotate(tank_transform2, 180)
			if direction == 'LEFT':
				image_tank2 = pygame.transform.rotate(tank_transform2, 90)
			if direction == 'RIGHT':
				image_tank2 = pygame.transform.rotate(tank_transform2, -90)
			screen.blit(image_tank2, (x, y))



	def restart():
		global kick_n, win_n, los_n
		user.register('room-29')
		user.turn_tank(user.token, 'UP')
		win_n = None
		los_n = None
		kick_n = None

	def winner():
		if player.response['winners'] != []:
			for win in player.response['winners']:
				if win['tankId'] == user.tank_id:
					score_win = win['score']
					return font.render("YOU WIN, YOUR SCORE: " + str(score_win) + "  PRESS R FOR RESTART", True, (211, 211, 255))
					

	def losers():
		if player.response['losers'] != []:
			for loser in player.response['losers']:
				if loser['tankId'] == user.tank_id:
					score_los = loser['score']
					return font.render("YOU LOSE, YOUR SCORE: " + str(score_los) + "   PRESS R FOR RESTART", True, (211, 211, 255))
						

	def kicked():

		if player.response['kicked'] != []:
			for kick in player.response['kicked']:
				if kick['tankId'] == user.tank_id:
					score_kick = kick['score']
					return font.render("YOU WAS KICKED, YOUR SCORE: " + str(score_kick) + "   PRESS R FOR RESTART", True, (211, 211, 255))


	def game_start():
		global kick_n, win_n, los_n
		done = True
		kick_n = None
		los_n = None
		win_n = None
		while done:
			screen.fill((0, 0, 0))
			background()
			if kick_n == None:
				kick_n = kicked()
			try:
				screen.blit(kick_n, (250, 250))
			except:
				pass
			if los_n == None:
				los_n = losers()
			try:
				screen.blit(los_n, (250, 250))
			except:
				pass
			if win_n == None:
				win_n = winner()
			try:
				screen.blit(win_n, (250, 250))
			except:
				pass

			panel()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done = False
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						done = False
					if event.key in MOVE_KEYS:
						user.turn_tank(user.token, MOVE_KEYS[event.key])
					if event.key == pygame.K_SPACE:
						user.fire_bullet(user.token)
					if event.key == pygame.K_r:
						restart()

						
			
			

			try:
				
				tanks = player.response['gameField']['tanks']
				for tank in tanks:
					draw_tank(**tank)
			except:
				pass
			
			try:
				bullets = player.response['gameField']['bullets']
				for bullet in bullets:
					draw_bullet(**bullet)
			except:
				pass
			
			
			pygame.display.flip()
		player.channel.stop_consuming()

	user = TankRPC()
	user.check_server_status()
	user.register('room-29')
	player = Player_consumer('room-29')
	player.start()
	user.turn_tank(user.token, 'UP')
	game_start()


def ai():
	IP = '34.254.177.17'
	PORT = 5672
	virthost = 'dar-tanks' 
	usname = 'dar-tanks'
	passw = '5orPLExUYnyVYZg48caMpX'


	pygame.init()
	screen = pygame.display.set_mode((1100, 600))
	font = pygame.font.Font('Wandery_Bold.ttf', 17)
	ss1 = pygame.mixer.Sound("sss.wav")



	class TankRPC:
		def __init__(self):
			self.connection = pika.BlockingConnection( 
				pika.ConnectionParameters(
					host = IP, 
					port = PORT, 
					virtual_host = virthost,
					credentials = pika.PlainCredentials(
						username = usname,
						password = passw)))
			self.channel = self.connection.channel()
			queue = self.channel.queue_declare(queue = '',
												auto_delete = True,
												exclusive = True)
			self.callback_queue = queue.method.queue
			self.channel.queue_bind(
				exchange = 'X:routing.topic',
				queue = self.callback_queue
				)
			self.channel.basic_consume(
				queue = self.callback_queue,
				on_message_callback = self.on_response,
				auto_ack = True)
			
			self.response = None
			self.corr_id = None
			self.token = None
			self.tank_id = None
			self.room_id = None
			self.x = 0
			self.y = 0


		def on_response(self, ch, method, props, body):
			if self.corr_id == props.correlation_id:
				self.response = json.loads(body)
				print(self.response)
			

		def call(self, key, message={}):
			self.response = None
			self.corr_id = str(uuid.uuid4())
			
			self.channel.basic_publish(
				exchange = 'X:routing.topic',
				routing_key = key,
				properties = pika.BasicProperties(
					reply_to = self.callback_queue,
					correlation_id = self.corr_id,
					),
				body = json.dumps(message))
			while self.response is None:
				self.connection.process_data_events()
				

		def check_server_status(self):
			self.call('tank.request.healthcheck')
			return self.response['status'] == '200'


		def register(self, room_id):
			message = {
			'roomId' : room_id
			}
			self.call('tank.request.register', message)
			if 'token' in self.response:
				self.token = self.response['token']
				self.tank_id = self.response['tankId']
				self.room_id = self.response['roomId']
				return True
			return False
				

		def turn_tank(self, token, direction):
			message = {
				'token' : token,
				'direction' : direction 
			}
			self.call('tank.request.turn', message)


		def fire_bullet(self, token):
			message = {
			'token': token
			}
			self.call('tank.request.fire', message)
			# if self.response['message'] == "You are firing too fast. A Tank can fire once per second.":
			# 	pygame.mixer.Sound.play(ss1)


	class Player_consumer(Thread):
		def __init__(self, room_id):
			super().__init__()
			self.connection = pika.BlockingConnection( 
				pika.ConnectionParameters(
					host = IP, 
					port = PORT, 
					virtual_host = virthost,
					credentials = pika.PlainCredentials(
						username = usname,
						password = passw)))
			self.channel = self.connection.channel()
			queue = self.channel.queue_declare(queue = '',
												auto_delete = True,
												exclusive = True)
			event_listener = queue.method.queue
			self.channel.queue_bind(exchange = 'X:routing.topic',
									queue = event_listener,
									routing_key = 'event.state.' + room_id)
			self.channel.basic_consume(
				queue = event_listener,
				on_message_callback = self.on_response, 
				auto_ack = True)
			self.response = None

		def on_response(self, ch, method, props, body):
			self.response = json.loads(body)
			print(self.response)

		def run(self):
			self.channel.start_consuming()



	UP = 'UP'
	DOWN = 'DOWN'
	LEFT = 'LEFT'
	RIGHT = 'RIGHT'

	MOVE_KEYS = {
		pygame.K_UP: UP,
		pygame.K_DOWN: DOWN,
		pygame.K_LEFT: LEFT,
		pygame.K_RIGHT: RIGHT
	}

	def background():
		back = pygame.image.load("background.png")
		back = pygame.transform.scale(back, (830, 600))
		screen.blit(back, (0, 0))

	def panel():
		border = pygame.image.load("border.png")
		border = pygame.transform.scale(border, (260, 600))
		screen.blit(border, (830, 0))
		ii = 0
		tank_list = []
		data_type = [('tank_id', int),('score', int), ('health', int)]
		for tank in player.response['gameField']['tanks']:
			temp = (int(tank['id'][5:]),tank['score'],tank['health'])
			tank_list.append(temp)
		tank_list_np = np.array(tank_list, dtype = data_type)
		tl_sorted = np.sort(tank_list_np, order =  ['score', 'health'])[::-1]

		for i in range(len(tl_sorted)):
			text_score = font.render("ID: {0}|  SCORE: {1} | HEALTH:  {2}".format(
				tl_sorted[i][0],
				tl_sorted[i][1],
				tl_sorted[i][2]),
				True, 
				(211, 211, 255))
			screen.blit(text_score, (840, ii + 180))
			ii += 25		

		


	def draw_bullet(x, y, width, height, direction, owner):
		bullet_im = pygame.image.load("bullet11.png")
		bullet_im2 = pygame.image.load("bullet22.png")
		bullet_im = pygame.transform.scale(bullet_im, (5, 15))
		bullet_im2 = pygame.transform.scale(bullet_im2, (5, 15))
		bullet_trans = bullet_im
		bullet_trans2 = bullet_im2
		if owner == user.tank_id:
			if direction == 'UP':
				bullet_im = bullet_trans
			if direction == 'LEFT':
				bullet_im = pygame.transform.rotate(bullet_trans, 90)
			if direction == 'RIGHT':
				bullet_im = pygame.transform.rotate(bullet_trans, -90)
			if direction == 'DOWN':
				bullet_im = pygame.transform.rotate(bullet_trans, 180)	
			screen.blit(bullet_im, (x, y))
		else:
			if direction == 'UP':
				bullet_im2 = bullet_trans2
			if direction == 'LEFT':
				bullet_im2 = pygame.transform.rotate(bullet_trans2, 90)
			if direction == 'RIGHT':
				bullet_im2 = pygame.transform.rotate(bullet_trans2, -90)
			if direction == 'DOWN':
				bullet_im2 = pygame.transform.rotate(bullet_trans2, 180) 
			screen.blit(bullet_im2, (x, y))

	def draw_tank(x, y, width, height, direction, score, health, id):
		tank_c = (x + int(width/2), y + int(width / 2))
		image_tank = pygame.image.load("tank_con.png")
		image_tank2 = pygame.image.load("tank_con_2.png")
		image_tank = pygame.transform.scale(image_tank, (width, height))
		image_tank2 = pygame.transform.scale(image_tank2, (width, height))
		tank_transform = image_tank
		tank_transform2 = image_tank2

		
		if id == user.tank_id:
			user.x = x
			user.y = y
			text = font.render("YOUR SCORE:" + str(score), True, (211, 211, 255))
			text2 = font.render("YOUR HEALTH:" + str(health), True, (211, 211, 255))
			text3 = font.render("TIME: " + str(player.response['remainingTime']), True, (211, 211, 255))
			screen.blit(text, (840, 25))
			screen.blit(text2, (840, 50))
			screen.blit(text3, (840, 75))
			if direction == 'UP':
				image_tank = tank_transform
			if direction == 'DOWN':
				image_tank = pygame.transform.rotate(tank_transform, 180)
			if direction == 'LEFT':
				image_tank = pygame.transform.rotate(tank_transform, 90)
			if direction == 'RIGHT':
				image_tank = pygame.transform.rotate(tank_transform, -90)
			screen.blit(image_tank, (x, y))
		else:

			if direction == 'UP':
				image_tank2 = tank_transform2
			if direction == 'DOWN':
				image_tank2 = pygame.transform.rotate(tank_transform2, 180)
			if direction == 'LEFT':
				image_tank2 = pygame.transform.rotate(tank_transform2, 90)
			if direction == 'RIGHT':
				image_tank2 = pygame.transform.rotate(tank_transform2, -90)
			screen.blit(image_tank2, (x, y))
	def restart():
		global kick_n, win_n, los_n
		user.register('room-29')
		user.turn_tank(user.token, 'UP')
		win_n = None
		los_n = None
		kick_n = None

	def winner():
		if player.response['winners'] != []:
			for win in player.response['winners']:
				if win['tankId'] == user.tank_id:
					score_win = win['score']
					return font.render("YOU WIN, YOUR SCORE: " + str(score_win) + "  PRESS R FOR RESTART", True, (211, 211, 255))
					

	def losers():
		if player.response['losers'] != []:
			for loser in player.response['losers']:
				if loser['tankId'] == user.tank_id:
					score_los = loser['score']
					return font.render("YOU LOSE, YOUR SCORE: " + str(score_los) + "   PRESS R FOR RESTART", True, (211, 211, 255))
						

	def kicked():
		if player.response['kicked'] != []:
			for kick in player.response['kicked']:
				if kick['tankId'] == user.tank_id:
					score_kick = kick['score']
					return font.render("YOU WAS KICKED, YOUR SCORE: " + str(score_kick) + "   PRESS R FOR RESTART", True, (211, 211, 255))

	def near_tank_find():
		global xe,ye,de
		hyp = 10000
		near_tank = ''
		xe,ye,de = 0, 0, "UP"

		for tank in player.response['gameField']['tanks']:
			if tank['id'] != user.tank_id:
				hyp_new = round(math.hypot( abs(user.x - tank['x']), abs( user.y - tank['y'])))
				if hyp_new < hyp:
					hyp = hyp_new			
					xe,ye,de = tank['x'], tank['y'], tank['direction']

	def near_bull_find():
		global xb,yb,db
		hypb = 10000
		near_bullet = ''
		for bullet in player.response['gameField']['bullets']:
			if bullet['owner'] != user.tank_id:
				hyp_newb = round(math.hypot( abs(user.x - bullet['x']), abs( user.y - bullet['y'])))
				if hyp_newb < hypb:
					hypb = hyp_newb	

					xb,yb,db = bullet['x'],bullet['y'],bullet['direction']
	# pygame.mixer.music.load("back.mp3")
	# pygame.mixer.music.play(-1)
	

	def game_start():

		global kick_n, win_n, los_n
		done = True
		kick_n = None
		los_n = None
		win_n = None

		while done:
			screen.fill((0, 0, 0))
			background()
			if kick_n == None:
				kick_n = kicked()
			try:
				screen.blit(kick_n, (250, 250))
			except:
				pass
			if los_n == None:
				los_n = losers()
			try:
				screen.blit(los_n, (250, 250))
			except:
				pass
			if win_n == None:
				win_n = winner()
			try:
				screen.blit(win_n, (250, 250))
			except:
				pass

			panel()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done = False
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						done = False
					if event.key in MOVE_KEYS:
						user.turn_tank(user.token, MOVE_KEYS[event.key])
					if event.key == pygame.K_SPACE:
						user.fire_bullet(user.token)
			if player.response['gameField']['bullets'] == []:
				xb = None
				yb = None
				db = None
			near_bull_find()			
			escape = True
			if xb == None:
				escape = True
			else:
				escape = False
			try:
				if escape == False:
					if yb < user.y and xb < user.x:
						if db == "UP" or db == "DOWN":
							user.turn_tank(user.token, UP)
						if db == "RIGHT" or db == "LEFT":
							user.turn_tank(user.token, "LEFT")
					if yb < user.y and xb > user.x:
						if db == "UP" or db == "DOWN":
							user.turn_tank(user.token, UP)
						if db == "RIGHT" or db == "LEFT":
							user.turn_tank(user.token, RIGHT)
					if yb > user.y and xb < user.x:
						if db == "UP" or db == "DOWN":
							user.turn_tank(user.token, DOWN)
						if db == "LEFT" or db == "RIGHT":
							user.turn_tank(user.token, LEFT)
					if yb > user.y and xb > user.x:
						if db == "UP" or db == "DOWN":
							user.turn_tank(user.token, DOWN)
						if db == "LEFT" or db == "RIGHT":
							user.turn_tank(user.token, RIGHT)

				
			except:
				pass
			near_tank_find()

			try:
				if escape == True:
					if ye < user.y and xe < user.x:
						if de == "UP" or de == "DOWN":
							user.turn_tank(user.token, UP)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, UP)
								user.fire_bullet(user.token)

							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, LEFT)
								user.fire_bullet(user.token)
						if de == "LEFT" or de == "RIGHT":
							user.turn_tank(user.token, LEFT)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, UP)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, UP)
								user.fire_bullet(user.token)
						

					if ye < user.y and xe > user.x:
						if de == "UP" or de == "DOWN":
							user.turn_tank(user.token, UP)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, UP)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, RIGHT)
								user.fire_bullet(user.token)
						if de == "LEFT" or de == "RIGHT":
							user.turn_tank(user.token, RIGHT)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, UP)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, UP)
								user.fire_bullet(user.token)

					if ye > user.y and xe < user.x:
						if de == "UP" or de == "DOWN":
							user.turn_tank(user.token, DOWN)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, DOWN)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, LEFT)
								user.fire_bullet(user.token)
						if de == "LEFT" or de == "RIGHT":
							user.turn_tank(user.token, LEFT)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, DOWN)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, LEFT)
								user.fire_bullet(user.token)

					if ye > user.y and xe > user.x:
						if de == "UP" or de == "DOWN":
							user.turn_tank(user.token, DOWN)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, DOWN)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, RIGHT)
								user.fire_bullet(user.token)
						if de == "LEFT" or de == "RIGHT":
							user.turn_tank(user.token, RIGHT)
							if xe >= user.x - 20 and xe <= user.x + 51:
								user.turn_tank(user.token, DOWN)
								user.fire_bullet(user.token)
							if ye >= user.y - 20 and ye <= user.y + 51:
								user.turn_tank(user.token, RIGHT)
								user.fire_bullet(user.token)
			except:
				pass
					
			try:
				tanks = player.response['gameField']['tanks']
				for tank in tanks:
					draw_tank(**tank)
			except:
				pass
			
			try:
				bullets = player.response['gameField']['bullets']
				for bullet in bullets:
					draw_bullet(**bullet)
			except:
				pass
			pygame.display.flip()


	user = TankRPC()
	user.check_server_status()
	user.register('room-28')
	player = Player_consumer('room-28')
	player.start()
	user.turn_tank(user.token, 'UP')
	game_start()

def single():

	screen = pygame.display.set_mode((800, 600))
	pygame.mixer.music.load("back.mp3")
	im4=pygame.image.load("dead_800_600.png")
	d1 = 1200
	d2 = 1200
	pygame.mixer.music.play(-1)
	ss = pygame.mixer.Sound("sss.wav")
	fruit1x = random.randint(0, 800)
	fruit1y = random.randint(0, 600)
	fruit2x = random.randint(0, 800)
	fruit2y = random.randint(0, 600)
	

	class wall():
		def __init__(self, x, y):
			self.width = 100
			self.height = 200
			self.x = x
			self.y = y
			self.wall = pygame.image.load("wall.png")
			self.wall = pygame.transform.scale(self.wall, (self.width, self.height))
		
		def draw(self, screen):
			screen.blit(self.wall, (self.x, self.y))

		def collision(self, tank, bullets):
			if tank.x + 120 < self.x + 100 and tank.x + 120 > self.x and tank.y + 60 > self.y and tank.y + 60 < self.y + 260 and tank.facing == "right":
				self.x = 2000
				self.y = 2000
				tank.score -= 1
			if tank.x < self.x + 100 and tank.x > self.x and tank.y + 60 > self.y and tank.y + 60 < self.y + 260 and tank.facing == "left":
				self.x = 2000
				self.y = 2000
				tank.score -= 1
			if tank.x + 60 > self.x and tank.x + 60 < self.x + 160 and tank.y > self.y and tank.y < self.y + 200 and tank.facing == "up":
				self.x = 2000
				self.y = 2000
				tank.score -= 1
			if tank.x + 60 > self.x and tank.x + 60 < self.x + 160 and tank.y + 120 > self.y and tank.y + 120 < self.y + 200 and tank.facing == "down":
				self.x = 2000
				self.y = 2000
				tank.score -= 1
			for bullet in bullets:
				if bullet.x > self.x and bullet.x + 5 < self.x + 100 and bullet.y > self.y and bullet.y + 5 < self.y + 200:
					self.x = 2000
					self.y = 2000 
					bullets.pop(bullets.index(bullet))


	class fruit():
		def __init__(self):
			self.x = random.randint(0,800)
			self.y = random.randint(0, 600)
			self.speed = 3
			self.clock = 0


		def draw(self, screen):
			pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), 10)

		def collision(self, tank, bullets):
			if (tank.x-8 <= self.x <= tank.x + 70 and tank.y-8 <= self.y <= tank.y + 130 and (tank.facing == "up" or tank.facing == "down") 
				or tank.x-8 <= self.x <= tank.x + 130 and tank.y-8 <= self.y <= tank.y + 70 and (tank.facing == "left" or tank.facing == "right")):
				self.x = 1100
				self.y = 1100
				tank.speed = 6
				tank.speed1 = 20
				self.clock = 0

				
	class snaryad():
		def __init__(self, x, y, facing, speed):
			self.x = x
			self.y = y
			self.facing = facing
			self.speed = speed
		def draw(self, screen):
			pygame.draw.circle(screen, (255 , 0, 0), (self.x, self.y), 5)


	class tank():
		def __init__(self, x, y, facing, img, t1x):
			self.x = x
			self.y = y
			self.facing = facing
			self.t1x = t1x
			self.img = img
			self.img = pygame.transform.scale(self.img, (60, 120))
			self.orig = self.img
			self.clock = 0
			self.font = pygame.font.Font(None,30)
			self.text = self.font.render(str("Жизни: "), True, (255,0,0))
			self.score = 3
			self.speed = 3
			self.speed1 = 10
			

		
		def draw(self):
			screen.blit(self.img, (self.x, self.y))
			text2 = self.font.render(str(self.score), True, (255,0,0))
			screen.blit(self.text, (self.t1x, 20))
			screen.blit(text2, (self.t1x + 100, 20))

		def transform(self, facing, angel):
			self.img = pygame.transform.rotate(self.orig, angel)
			self.facing = facing

		def move(self):
			if self.facing == "right": 	self.x += self.speed 
			if self.facing == "left":	self.x -= self.speed
			if self.facing == "up":		self.y -= self.speed
			if self.facing == "down":	self.y += self.speed
			if self.x <= -120: 			self.x = 790
			if self.x >= 800: 		self.x = -110 
			if self.y >= 600: 		self.y = -100
			if self.y <= -120: 		self.y = 590

	def draw_back():
		back_sing = pygame.image.load("background.png")
		back_sing = pygame.transform.scale(back_sing, (800, 600))
		screen.blit(back_sing, (0, 0))

	def collision(bullets, t2):
		for bullet in bullets:
			if bullet.x >= t2.x and bullet.x <= t2.x + 125 and bullet.y >= t2.y and bullet.y <= t2.y + 65 and t2.facing == "right" :
				t2.score -= 1
				bullets.pop(bullets.index(bullet))	
			if bullet.x >= t2.x and bullet.x <= t2.x + 125 and bullet.y >= t2.y and bullet.y <= t2.y + 65 and t2.facing == "left" :
				t2.score -= 1
				bullets.pop(bullets.index(bullet))
			if bullet.x >= t2.x and bullet.x <= t2.x + 65 and bullet.y >= t2.y and bullet.y <= t2.y + 120 and t2.facing == "up" :
				t2.score -= 1
				bullets.pop(bullets.index(bullet))
			if bullet.x >= t2.x and bullet.x <= t2.x + 65 and bullet.y >= t2.y and bullet.y <= t2.y + 120 and t2.facing == "down" :
				t2.score -= 1
				bullets.pop(bullets.index(bullet))


	def bull_move(self):
		for bullet in self :
			if bullet.x <= 800 and bullet.x>= 0 and bullet.y >=0 and bullet.y<=600:
				if bullet.facing == "right":	
					bullet.x += bullet.speed 
				if bullet.facing == "left":	
					bullet.x -= bullet.speed
				if bullet.facing == "up":		
					bullet.y -= bullet.speed
				if bullet.facing == "down":	
					bullet.y += bullet.speed
			else:
				self.pop(self.index(bullet))

	def bull_add(self, instance, x, y):
		bull_x = self.x + x
		bull_y = self.y + y 
		if len(instance) < 5:
			instance.append(snaryad(bull_x, bull_y, self.facing, self.speed1))



	done2 = False
	fontd = pygame.font.Font('Wandery_Bold.ttf', 35)
	text_dead = fontd.render('First player win', True, (255,0,0))
	text_dead1 = fontd.render('Second player win', True, (255,0,0))

	t1_img = pygame.image.load("tank_sig.png")
	t2_img = pygame.image.load("tank_sig_2.png")
	bullets = []
	bullets2 = []
	FPS = 60
	clock = pygame.time.Clock()
	fruits = fruit()
	interval = random.randint(400, 900)

	w1 = wall(random.randint(0, 700), 400)
	w2 = wall(random.randint(0, 700), 400)
	w3 = wall(random.randint(0, 700), 100)

	t1 = tank(700,500,'up', t1_img, 650)
	t2 = tank(100,100,'up', t2_img, 0)


	while not done2:
		
	
		mill = clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				done2 = True
				pygame.mixer.music.pause()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN and t1.facing == "up":
					bull_add(t1, bullets, 27, -5)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_RETURN and t1.facing == "right":
					bull_add(t1, bullets, 120, 27)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_RETURN and t1.facing == "down" :
					bull_add(t1, bullets, 27, 120)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_RETURN and t1.facing == "left" :
					bull_add(t1, bullets, -5, 27)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_SPACE and t2.facing == "up":
					bull_add(t2, bullets2, 27, -5)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_SPACE and t2.facing == "right":
					bull_add(t2, bullets2, 120, 27)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_SPACE and t2.facing == "down" :
					bull_add(t2, bullets2, 27, 120)
					pygame.mixer.Sound.play(ss)
				if event.key == pygame.K_SPACE and t2.facing == "left" :
					bull_add(t2, bullets2, -5, 27)
					pygame.mixer.Sound.play(ss)

		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				done2 = True
				pygame.mixer.music.pause()
			elif event.key == pygame.K_RIGHT:
				t1.transform("right", -90)
			elif event.key == pygame.K_LEFT:
				t1.transform("left", 90)
			elif event.key == pygame.K_UP:
				t1.transform("up", 0)
			elif event.key == pygame.K_DOWN:
				t1.transform("down", 180)
			elif event.key == pygame.K_a:
				t2.transform("left", 90)
			elif event.key == pygame.K_d:
				t2.transform("right", -90)
			elif event.key == pygame.K_w:
				t2.transform("up", 0)
			elif event.key == pygame.K_s:
				t2.transform("down", 180)
		



		bull_move(bullets)
		bull_move(bullets2)

		t1.move()
		t2.move()
		
		screen.fill((0, 0, 0))
		draw_back()
		t1.draw()
		t2.draw()


		if t1.speed == 6:
			t1.clock += 1
			if t1.clock == 322:
				t1.clock = 0
				t1.speed = 3
				t1.speed1 = 10

		if t2.speed == 6:
			t2.clock += 1
			if t2.clock == 322:
				t2.clock = 0
				t2.speed = 3
				t2.speed1 = 10

		collision(bullets, t2)
		collision(bullets2, t1)
		for bullet in bullets:
			bullet.draw(screen)
		for bullet in bullets2:
			bullet.draw(screen)

		if fruits.x == 1100 and fruits.y == 1100:
			fruits.clock += 1
			if fruits.clock == interval:
				fruits.x = random.randint(0, 800)
				fruits.y = random.randint(0, 600)
				fruits.clock = 0
		fruits.draw(screen)


		fruits.collision(t1, bullets)
		fruits.collision(t2, bullets2)


		w1.draw(screen)
		w1.collision(t1, bullets)
		w1.collision(t2, bullets2)
		w2.draw(screen)
		w2.collision(t1, bullets)
		w2.collision(t2, bullets2)
		w3.draw(screen)
		w3.collision(t1, bullets)
		w3.collision(t2, bullets2)

		screen.blit(im4, (d1, d2))
		if t2.score <= 0:
			d1 = 0
			d2 = 0
			screen.blit(im4, (d1, d2))
			screen.blit(text_dead, (250, 100))
		if t1.score <= 0:
			d1 = 0
			d2 = 0
			screen.blit(im4, (d1, d2))
			pygame.mixer.music.pause
			screen.blit(text_dead1, (250, 100))
		pygame.display.update()
		pygame.display.flip()

class menu():

	def __init__(self, x, y, image, text, text_x, text_y, press):
		self.x = x
		self.y = y 
		self.text_x = text_x
		self.text_y = text_y
		self.image = image
		self.text = text
		self.press = press

	def draw(self):
		
		screen.blit(self.image, (self.x, self.y))
		screen.blit(self.text, (self.text_x, self.text_y))
		

	def check_press(self):
		if pygame.mouse.get_pressed() == (1, 0, 0):
			position = pygame.mouse.get_pos()
			if position[0] >= self.x and position[0] <= self.x + 200 and position[1] >= self.y and position[1] <= self.y + 100:
				first = False
				self.press()



back = pygame.image.load("background.png")
button1 = pygame.image.load("button1.png")
button1 = pygame.transform.scale(button1, (200, 100))
button2 = pygame.image.load("button1.png")
button2 = pygame.transform.scale(button2, (200, 100))
button3 = pygame.image.load("button1.png")
button3 = pygame.transform.scale(button3, (200, 100))
font = pygame.font.Font('Wandery_Bold.ttf', 17)
text1 = font.render("SINGLEPLAYER", True, (11, 11, 55))
text2 = font.render("MULTIPLAYER", True, (11, 11, 55))
text3 = font.render("AI MULTIPLAYER", True, (11, 11, 55))
button = []
button.append(menu(300, 100, button1, text1, 340, 143, single))
button.append(menu(300, 250, button2, text2, 348, 293, multi))
button.append(menu(300, 400, button3, text3, 335, 443, ai))
done = True
first = True



while done:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = False
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				done = False
	

	

	screen.blit(back, (0, 0))
	if first == True:
		for men in button:
			men.draw()
			men.check_press()
	pygame.display.update()
	pygame.display.flip()
	