from models import Base
from services.database import engine

Base.metadata.create_all(engine)
