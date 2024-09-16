from sqlalchemy import Column, Integer, String, Text
from database import Base

class ScrapedData(Base):
    __tablename__ = 'scraped_data'

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), unique=True)  # URL of the website being scraped
    title = Column(String(255))  # Title of the webpage
    content = Column(Text)  # The content we scrape (unlimited length)