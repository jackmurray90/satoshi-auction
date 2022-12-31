from flask import Flask, redirect, request, render_template, make_response
from db import Auction, RateLimit, Height, engine
from sqlalchemy.orm import Session
from rate_limit import rate_limit
from bitcoin import get_new_address, get_height

app = Flask(__name__)

@app.route('/')
def index():
  with Session(engine) as session:
    height = session.query(Height).one().height
    auctions = session.query(Auction).where(Auction.deadline > height).order_by(Auction.prize.desc()).all()
    return render_template(
        'index.html',
        auctions=[{
          'auction_id': auction.id,
          'prize': auction.prize,
          'maximum_bid': auction.maximum_bid,
          'deadline': auction.deadline if auction.deadline > height else None,
          'address': auction.address,
          } for auction in auctions]
      )

@app.route('/auction/<auction_id>')
def auction(auction_id):
  rate_limit()
  with Session(engine) as session:
    try:
      [auction] = session.query(Auction).where(Auction.id == auction_id)
    except:
      return 'Auction not found.'
    height = session.query(Height).one().height
    return render_template(
        'auction.html',
        auction_id=auction.id,
        prize=auction.prize,
        deadline=auction.deadline if auction.deadline > height else None,
        address=auction.address,
        winners=[{ 'payout_address': winner.payout_address, 'bid': winner.bid } for winner in auction.participants if winner.bid == auction.maximum_bid]
        )

@app.route('/auctions')
def auctions():
  rate_limit()
  with Session(engine) as session:
    auctions = session.query(Auction).order_by(Auction.id.desc()).all()
    height = session.query(Height).one().height
    return render_template(
        'index.html',
        auctions=[{
          'auction_id': auction.id,
          'prize': auction.prize,
          'maximum_bid': auction.maximum_bid,
          'deadline': auction.deadline if auction.deadline > height else None,
          'address': auction.address,
          } for auction in auctions]
      )
