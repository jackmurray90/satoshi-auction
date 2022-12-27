from flask import Flask, request, render_template, make_response
from db import Game, RateLimit, engine
from sqlalchemy.orm import Session
from rate_limit import rate_limit
from bitcoin import get_new_address, valid_bitcoin_address

app = Flask(__name__)

@app.route('/')
def index():
  with Session(engine) as session:
    games = session.query(Game).all()
    empty_games = 0
    for game in games:
      if all([player.bet == 0 for player in game.players]):
        empty_games += 1
    return render_template('coinballer.html', total_games=len(games), empty_games=empty_games)

@app.route('/coinballer')
def coinballer():
  rate_limit()
  response = make_response(render_template('coinballer'))
  response.headers['Content-type'] = 'application/octet-stream; charset=utf-8'
  return response

@app.route('/new_game')
def new_game():
  rate_limit()
  addresses = [address for address in request.args]
  for address in addresses:
    if len([a for a in addresses if a == address]):
      return 'Player addresses must be unique'
    if not valid_bitcoin_address:
      return address + ' is not a valid bitcoin address'
  with Session(engine) as session:
    game = Game(height=get_height())
    session.add(game)
    for address in addresses:
      session.add(Player(game=game, betting_address=get_new_address(), payout_address=address, bet=0))
    session.commit()
    return render_template('new_game.txt', game_id=game.id)

@app.route('/status')
def status():
  rate_limit()
  with Session(engine) as session:
    try:
      [game] = session.query(Game).where(Game.id == request.args['game_id'])
    except:
      return 'Game not found.'
    players = [{
        'betting_address': player.betting_address,
        'payout_address': player.payout_address,
        'bet': player.bet
      } for player in game.players]
    return render_template('status.html', game_id=game.id, height=game.height, players=players)
