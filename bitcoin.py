from sqlalchemy.orm import Session
from db import Game, Player, Height
from sqlalchemy import create_engine
from time import sleep
from env import DB
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from math import floor
from decimal import Decimal
from env import BITCOIN, DB
from http.client import CannotSendRequest
from hashlib import sha256

MINCONF = 2


def get_height():
  while True:
    try:
      rpc = AuthServiceProxy(BITCOIN)
      return rpc.getblockcount() - MINCONF
    except:
      sleep(1)

def get_incoming_txs(height):
  while True:
    try:
      rpc = AuthServiceProxy(BITCOIN)
      txs = rpc.listsinceblock(rpc.getblockhash(height-1))
      incoming_txs = []
      for tx in txs['transactions']:
        if tx['category'] == 'receive' and tx['blockheight'] == height:
          incoming_txs.append((tx['address'], tx['amount']))
      return incoming_txs
    except:
      sleep(1)

def send(address, amount):
  while True:
    try:
      rpc = AuthServiceProxy(BITCOIN)
      rpc.send({address: amount})
    except:
      sleep(1)

def get_new_address():
  while True:
    try:
      rpc = AuthServiceProxy(BITCOIN)
      return rpc.getnewaddress()
    except:
      sleep(1)

def round_down(amount):
  return floor(amount * 10**8) / Decimal(10**8)

if __name__ == '__main__':
  with Session(create_engine(DB)) as session:
    while True:
      height = session.query(Height).one().height
      while height < get_height():
        for address, amount in get_incoming_txs(height):
          try:
            [player] = session.query(Player).where(Player.betting_address == address)
          except:
            continue
          if not player.game.finished:
            player.bet += amount
            player.game.height = height
            player.game.pot += amount
            session.commit()
        games = session.query(Game).where(Game.height == height - 144)
        for game in games:
          winners = []
          for player in game.players:
            if player.bet == max([p.bet for p in players]):
              winners.append(player)
          payout = round_down(sum([p.bet for p in players]) * Decimal('0.98') / len(winners))
          for winner in winners:
            send(winner.payout_address, payout)
          game.finished = True
          session.commit()
      sleep(1)
