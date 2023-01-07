from flask import Flask, redirect, request, render_template, make_response
from db import Auction, RateLimit, Height, engine
from sqlalchemy.orm import Session
from rate_limit import rate_limit
from bitcoin import get_new_address, get_height, get_real_height, get_unconfirmed_participants
from geoip import is_australia
from decimal import Decimal
from math import floor

app = Flask(__name__)

@app.template_filter()
def format_decimal(d, decimal_places):
  digit = Decimal('10')
  while digit <= d:
    digit *= 10
  result = ''
  while decimal_places:
    result += str(floor(d % digit * 10 / digit))
    digit /= 10
    if digit == 1:
      result += '.'
    if digit < 1:
      decimal_places -= 1
  return result

@app.route('/')
def index():
  if is_australia(): return redirect('/australia')
  with Session(engine) as session:
    height = session.query(Height).one().height
    auctions = session.query(Auction).where(Auction.deadline > height).order_by(Auction.prize.desc()).all()
    real_height = get_real_height()
    return render_template(
        'index.html',
        auctions=[{
          'auction_id': auction.id,
          'prize': auction.prize,
          'maximum_bid': auction.maximum_bid,
          'countdown': auction.deadline - real_height if auction.deadline > real_height else 'Auction is finished',
          'address': auction.address,
          } for auction in auctions]
      )

@app.route('/rules')
def rules():
  if is_australia(): return redirect('/australia')
  return render_template('rules.html')

@app.route('/about')
def about():
  if is_australia(): return redirect('/australia')
  return render_template('about.html')

@app.route('/auction/<auction_id>')
def auction(auction_id):
  rate_limit()
  if is_australia(): return redirect('/australia')
  with Session(engine) as session:
    try:
      [auction] = session.query(Auction).where(Auction.id == auction_id)
    except:
      return 'Auction not found.'
    height = session.query(Height).one().height
    countdown = auction.deadline - get_real_height()
    if countdown < 0:
      countdown = 'Auction is finished'
    participants = dict([(p.payout_address, {'payout_address': p.payout_address, 'bid': p.bid}) for p in auction.participants])
    for p in get_unconfirmed_participants(auction.address):
      if p['payout_address'] in participants:
        if p['bid'] > participants[p['payout_address']]['bid']:
          participants[p['payout_address']]['bid'] = p['bid']
      else:
        participants[p['payout_address']] = p
    return render_template(
        'auction.html',
        auction_id=auction.id,
        prize=auction.prize,
        countdown=countdown,
        address=auction.address,
        participants=[participants[p] for p in participants]
        )

@app.route('/auctions')
def auctions():
  rate_limit()
  if is_australia(): return redirect('/australia')
  with Session(engine) as session:
    height = session.query(Height).one().height
    auctions = session.query(Auction).where(Auction.deadline <= height).order_by(Auction.id.desc()).all()
    return render_template(
        'auctions.html',
        auctions=[{
          'auction_id': auction.id,
          'prize': auction.prize,
          'maximum_bid': auction.maximum_bid,
          } for auction in auctions]
      )

@app.route('/australia')
def australia():
  return render_template('australia.html')
