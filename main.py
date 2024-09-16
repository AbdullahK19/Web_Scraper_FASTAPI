import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated, List
import re
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


# Pydantic model for scraping request
class ScrapeRequest(BaseModel):
    url: str  # URL to scrape

# Pydantic model for the scraped data response
class ScrapedDataBase(BaseModel):
    url: str
    title: str
    content: str


# Dependency for the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# Function to scrape a website
def scrape_website(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching the URL: {e}")

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Extracting the title
    title = soup.title.string if soup.title else "No title found"
    
    # Extracting the main content
    main_content = ""
    
    # Try common content containers
    for selector in ['main', 'article', 'div.content', 'div.main', 'div#main', 'div.article']:
        content_div = soup.select_one(selector)
        if content_div:
            main_content = content_div.get_text()
            break
    
    # If main content is still empty, fall back to body text
    if not main_content:
        main_content = soup.body.get_text() if soup.body else soup.get_text()

    # Clean up the text
    # Remove excessive newlines and multiple spaces
    cleaned_content = re.sub(r'\s+', ' ', main_content).strip()
    
    # Limit content to the first 1000 characters for example
    content = cleaned_content[:1000]

    return {"title": title, "content": content}


# Route to scrape a website and store the result in the database
@app.post("/scrape/", status_code=status.HTTP_201_CREATED)
async def scrape_and_store(data: ScrapeRequest, db: db_dependency):
    # Check if the data for the given URL already exists in the database
    existing_entry = db.query(models.ScrapedData).filter(models.ScrapedData.url == data.url).first()
    if existing_entry:
        raise HTTPException(status_code=400, detail="Data for this URL already exists")

    # Scrape the website
    scraped_data = scrape_website(data.url)

    # Store the scraped data in the database
    db_data = models.ScrapedData(
        url=data.url,
        title=scraped_data["title"],
        content=scraped_data["content"]
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)

    return db_data


# Route to get a specific scraped entry by ID
@app.get("/scrape/{scrape_id}", status_code=status.HTTP_200_OK, response_model=ScrapedDataBase)
async def read_scraped_data(scrape_id: int, db: db_dependency):
    scraped_data = db.query(models.ScrapedData).filter(models.ScrapedData.id == scrape_id).first()
    if scraped_data is None:
        raise HTTPException(status_code=404, detail="Scraped data not found")
    return scraped_data


# Route to get all scraped data (optional)
@app.get("/scrape/", status_code=status.HTTP_200_OK, response_model=List[ScrapedDataBase])
async def get_all_scraped_data(db: db_dependency):
    scraped_data_list = db.query(models.ScrapedData).all()
    return scraped_data_list


# Route to delete a specific scraped entry by ID
@app.delete("/scrape/{scrape_id}", status_code=status.HTTP_200_OK)
async def delete_scraped_data(scrape_id: int, db: db_dependency):
    scraped_data = db.query(models.ScrapedData).filter(models.ScrapedData.id == scrape_id).first()
    if scraped_data is None:
        raise HTTPException(status_code=404, detail="Scraped data not found")
    db.delete(scraped_data)
    db.commit()
    return {"detail": "Scraped data deleted successfully"}


# Route to search for specific keywords in the scraped data
@app.get("/search/", response_model=List[ScrapedDataBase])
async def search_scraped_data(keyword: str, db: db_dependency):
    results = db.query(models.ScrapedData).filter(models.ScrapedData.content.ilike(f'%{keyword}%')).all()
    return results