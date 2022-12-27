from sqlalchemy import create_engine
from db import Base
from env import DB

if __name__ == '__main__':
  engine = create_engine(DB)
  Base.metadata.create_all(engine)
