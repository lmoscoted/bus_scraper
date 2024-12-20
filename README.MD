## Bus Scraper Project

This is the readme file for the bus scraper project, which utilizes Scrapy to extract bus listings and details from absolutebus.com.

**Project Structure:**
```
bus_scraper/
├── __init__.py 
├── items.py      # Defines data structures for scraped data
├── middlewares.py  # Custom middleware for user agent, error handling, etc.
├── models.py       # Database models for storing scraped data (optional)
├── pipelines.py    # Pipeline for persisting data (e.g., database)
├── requirements.txt # Lists required Python packages
├── scrapy.cfg      # Optional Scrapy configuration file
├── scrapy_log.txt  # Log file for Scrapy activities
├── settings.py     # Scrapy project settings
└── spiders/
    ├── __init__.py 
    └── bus_spider.py  # Spider class for scraping bus listings and details
```

**Dependencies:**

This project requires the following Python packages:

- scrapy
- pydantic (for data validation in items)
- sqlalchemy (for database integration)

Also, it use Mysql 8.0  as a database.


**Instructions:**
1. **Create and activate virtual environment:** Run `python -m venv venv` and then activate it. 
2. **Install dependencies:** Run `pip install -r requirements.txt` to install the required packages.
3. **Creare .env file for database persistance:** Copy the .env.copy file and paste in the same place with the name .env. Then, update the database settings accordingly. 
3. **Run the scraper:** Execute `scrapy crawl bus_spider` to initiate the scraping process. Scraped data will be saved as Json file called `raw_buses`.

After that, a json and log file will be created and the pipeline that has in charge of processing and persisting the scraped data will run. Finally, the scraped data will be available in the tables: `buses`, `buses_overview`, `buses_image`.


**Approach:**

This scraper utilizes Scrapy's features to efficiently extract bus data:

- **BusSpider:** This spider class defines the scraping logic.
    - Starts by scraping the listings page, extracting basic information like title, source URL, and a flag indicating if the bus is sold.
    - Follows links to individual bus detail pages for further information.
    - Extracts details like images, descriptions, price, air conditioning availability, passenger capacity, mileage, engine/transmission details, gross weight, wheelchair accessibility, and luggage compartments.
- **Items:** The `items.py` file defines data structures (Item classes) for scraped data using Pydantic (optional). These classes hold scraped information in a structured format.
- **Middleware:** The `middlewares.py` file allows for customization of Scrapy behavior. It implements custom middleware for:
    - User-Agent rotation to avoid website blocking.
    - Exponential backoff for retrying failed requests.
- **Pipeline:** The `pipelines.py` file defines the data persistence mechanism. This project includes an example pipeline (`MySQLPipeline`) that demonstrates how to save scraped data to a MySQL database using SQLAlchemy. 

**Database Dump:**

In the root folder there is a database dump sql file that contains the scrapped data for all the three tables called `dump-busesforsale.sql`.

**Error Handling and Retry Logic:**

- The `settings.py` file configures Scrapy with robust error handling and retry logic.
- It defines settings for:
    - Retrying failed requests with exponential backoff (`RETRY_TIMES`, `RETRY_INITIAL_DELAY`)
    - Handling specific exceptions like connection errors and timeouts (`RETRY_EXCEPTIONS`)
    - HTTP status codes to retry on (`RETRY_HTTP_CODES`)
- Scrapy logs any errors encountered during the scraping process.

**Performance and Scalability:**

- The spider leverages Scrapy's built-in features for efficient crawling:
    - Follows links to individual detail pages from the listings page.
    - Employs asynchronous processing for faster performance.
- The `settings.py` file can be configured with:
    - `CONCURRENT_REQUESTS` to control the number of concurrent requests (default: 16).
    - `DOWNLOAD_DELAY` to introduce a delay between requests to avoid overwhelming the server (default: 0).
- For large-scale scraping, consider distributed scraping solutions offered by Scrapy Cluster or ScrapyD. Also, we can change the Feed output to jsonlines for handling large datasets. 


**Limitations:**

- This scraper is currently designed to work with absolutebus.com and might require modifications for other websites.
- The chosen data persistence method (e.g., database) will impact scalability.
- The effectiveness of scraping techniques may change over time as website structures evolve.

**Additional Notes:**

- The code includes helper functions defined outside the spider class to handle specific data extraction tasks (e.g., extracting images, price, air conditioning).
- In the case that this scraper is used for more than one website source, we can have cases when a bus is pusblished in more than once on a website, we should take into consideration using a mechanism for detecting if it is the same item.
- I consider that the generated json file should be placed in a landing zone such as S3 bucket, then start the processing and the storing of the data. We can use events and queues for implementing this ETL process. Doing in this way, the system will be more isolated, robust and reliable.
