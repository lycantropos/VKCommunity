from models import Base
from services.data_access import DataAccessObject
from settings import DATABASE_URL

dao = DataAccessObject(DATABASE_URL)
Base.metadata.create_all(dao.engine)
