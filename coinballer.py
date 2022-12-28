from flask import Flask, request, render_template, make_response
from db import Game, RateLimit, engine
from sqlalchemy.orm import Session
from rate_limit import rate_limit
from bitcoin import get_new_address, get_height

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

@app.route('/new_game', methods=['GET', 'POST'])
def new_game():
  rate_limit()
  if not request.form.get('addresses'):
    return render_template('new_game.html')
  addresses = [address for address in request.form['addresses'].strip().split()]
  for address in addresses:
    if len([a for a in addresses if a == address]) > 1:
      return 'Player addresses must be unique'
    if len(address) > 128:
      return 'Invalid bitcoin address'
  with Session(engine) as session:
    game = Game(height=get_height(), finished=False)
    session.add(game)
    for address in addresses:
      session.add(Player(game=game, betting_address=get_new_address(), payout_address=address, bet=0))
    session.commit()
    return redirect('/game/%d' % game.id)

@app.route('/game/<game_id>')
def game(game_id):
  rate_limit()
  with Session(engine) as session:
    try:
      [game] = session.query(Game).where(Game.id == game_id)
    except:
      return 'Game not found.'
    players = [{
        'betting_address': player.betting_address,
        'payout_address': player.payout_address,
        'bet': player.bet
      } for player in game.players]
    return render_template('game.html', game_id=game.id, height=game.height, players=players)

@app.route('/games')
def games():
  rate_limit()
  with Session(engine) as session:
    games = session.query(Game).where(Game.finished == False)
    def calculate_pot(game):
      players = session.query(Player).where(Player.game == game)
      return sum([player.bet for player in players])
    games = [{
      'game_id': game.id,
      'pot': calculate_pot(game),
      'status': 'Active' if not game.finished else 'Finished'
      } for game in games]
    return render_template('games.html', games=games)
