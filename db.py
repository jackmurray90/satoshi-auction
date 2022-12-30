from sqlalchemy import Integer, Boolean, Numeric, Column, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship
from env import DB

Base = declarative_base()

class Auction(Base):
  __tablename__ = 'auctions'

  id = Column(Integer, primary_key=True)
  address = Column(String)
  deadline = Column(Integer)
  participants = relationship('Participant')
  maximum_bid = Column(Numeric(16, 8))
  prize = Column(Numeric(16, 8), default=0)

class Participant(Base):
  __tablename__ = 'participants'

  id = Column(Integer, primary_key=True)
  auction_id = Column(Integer, ForeignKey('auctions.id'))
  payout_address = Column(String)
  bid = Column(Numeric(16, 8))
  auction = relationship('Auction', back_populates='participants')

class Height(Base):
  __tablename__ = 'height'

  height = Column(Integer, primary_key=True)

class RateLimit(Base):
  __tablename__ = 'ratelimit'

  address = Column(String, primary_key=True)
  timestamp = Column(Numeric(17, 5))

engine = create_engine(DB)
