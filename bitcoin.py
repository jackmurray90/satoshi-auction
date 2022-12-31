from sqlalchemy.orm import Session
from db import Auction, Participant, Height
from sqlalchemy import create_engine
from time import sleep
from env import DB
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from math import floor
from decimal import Decimal
from env import BITCOIN, DB
from http.client import CannotSendRequest
from hashlib import sha256
from bitcoinrpc.authproxy import JSONRPCException

MINCONF = 3

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
          rawtx = rpc.getrawtransaction(tx['txid'], True)
          return_address = None
          for vin in rawtx['vin']:
            try:
              txid = vin['txid']
            except:
              continue
            out = rpc.getrawtransaction(txid, True) # the transaction that sent to us
            try:
              return_address = out['vout'][vin['vout']]['scriptPubKey']['address']
              break
            except:
              continue
          if return_address:
            incoming_txs.append((tx['address'], return_address, tx['amount']))
      return incoming_txs
    except Exception as e:
      sleep(1)

def send(address, amount):
  while True:
    try:
      rpc = AuthServiceProxy(BITCOIN)
      return rpc.send({address: amount})
    except JSONRPCException:
      return
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
      heightstore = session.query(Height).one()
      height = heightstore.height
      while height < get_height():
        print("Processing height", height)
        for address, return_address, amount in get_incoming_txs(height):
          print("Processing bid from", return_address, "to", address, "for", amount)
          try:
            [auction] = session.query(Auction).where(Auction.address == address)
          except:
            continue
          if auction.deadline < height:
            continue
          participant = None
          for p in auction.participants:
            if p.payout_address == return_address:
              participant = p
              break
          if participant:
            if participant.bid < amount:
              participant.bid = amount
          else:
            session.add(Participant(auction=auction, payout_address=return_address, bid=amount))
          auction.deadline = height + 144
          auction.prize += round_down(amount * Decimal('0.98'))
          auction.maximum_bid = max(auction.maximum_bid, amount)
          session.commit()
        auctions = session.query(Auction).where(Auction.deadline == height)
        for auction in auctions:
          winners = []
          for participant in auction.participants:
            if participant.bid == auction.maximum_bid:
              winners.append(participant)
          if len(winners) > 0:
            payout = auction.prize / len(winners)
            for winner in winners:
              send(winner.payout_address, payout)
        running_auctions = session.query(Auction).where(Auction.deadline > height).count()
        if running_auctions < 5:
          for i in range(5 - running_auctions):
            session.add(Auction(address=get_new_address(), deadline=height+144, maximum_bid=0, prize=Decimal('0.00010000')))
        heightstore.height += 1
        height = heightstore.height
        session.commit()
        sleep(1)
