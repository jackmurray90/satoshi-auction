from flask import Flask, redirect, request, render_template, make_response
from db import Auction, RateLimit, Height, engine
from sqlalchemy.orm import Session
from rate_limit import rate_limit
from bitcoin import get_new_address, get_height

app = Flask(__name__)

@app.route('/')
def index():
  with Session(engine) as session:
    return render_template('index.html')

@app.route('/auction/<auction_id>')
def auction(auction_id):
  rate_limit()
  with Session(engine) as session:
    try:
      [auction] = session.query(Auction).where(Auction.id == auction_id)
    except:
      return 'Auction not found.'
    height = session.query(Height).one()
    return render_template(
        'auction.html',
        auction_id=auction.id,
        prize=auction.prize,
        deadline=auction.deadline if auction.deadline > height else None,
        address=auction.address,
        participants=[{ 'payout_address': participant.payout_address, 'bid': participant.bid } for participant in auction.participants]
        )

@app.route('/auctions')
def auctions():
  rate_limit()
  with Session(engine) as session:
    auctions = session.query(Auction).order_by(Auction.deadline.desc()).all()
    height = session.query(Height).one().height
    auctions = [{
      'auction_id': auction.id,
      'prize': auction.prize,
      'maximum_bid': auction.maximum_bid,
      'deadline': auction.deadline if auction.deadline > height else None,
      } for auction in auctions]
    return render_template('auctions.html', auctions=auctions)
