# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem, CloseSpider
from scrapy.loader import ItemLoader
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from itemadapter import ItemAdapter


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from bus_scraper.models import (
    Base,
    Bus,
    BusTable,
    BusesImageTable,
    BusesOverviewTable,
)


class BusScraperPipeline:
    def process_item(self, item, spider):
        return item


"""
MySQL pipeline for Scrapy.

This pipeline connects to a MySQL database using a provided URL, creates all necessary tables
if they don't exist, and saves scraped items into the database. It performs upsert operations
on related tables (`BusTable`, `BusesImageTable`, and `BusesOverviewTable`) for efficient data
persistence.

Attributes:
    database_url (str): The URL of the MySQL database to connect to.
    engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance for database connection.
    Session (sqlalchemy.orm.sessionmaker): A sessionmaker object for creating database sessions.
"""


class MySQLPipeline:
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        self.Session = None

    @classmethod
    def from_crawler(cls, crawler):
        database_url = crawler.settings.get(
            "DATABASE_URL"
        )  # Correct way to access settings
        if not database_url:
            raise CloseSpider("DATABASE_URL setting is not defined.")
        return cls(database_url)

    def open_spider(self, spider):
        spider.logger.info(f"Connecting to database: {self.database_url}")
        try:
            self.engine = create_engine(self.database_url, echo=False)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            spider.logger.error(f"Database connection error: {e}")
            raise CloseSpider("Database connection failed")

    def close_spider(self, spider):
        if self.engine:
            self.engine.dispose()
            spider.logger.info("Database connection closed.")

    def process_item(self, item, spider):
        bus_data = Bus(**ItemAdapter(item).asdict())
        session = self.Session()

        try:
            # Upsert BusTable
            bus_table = session.merge(
                BusTable(**bus_data.model_dump(exclude={"images", "bus_overview"}))
            )
            session.flush()  # Flush to get the bus_table.id

            if bus_data.images:
                for image_data in bus_data.images:
                    image_table = BusesImageTable(**image_data.model_dump())
                    image_table.bus_id = bus_table.id
                    session.merge(image_table)

            if bus_overview_data := bus_data.bus_overview:
                bus_overview_table = BusesOverviewTable(
                    **bus_overview_data.model_dump()
                )
                bus_overview_table.bus_id = bus_table.id
                session.merge(bus_overview_table)

            session.commit()
            spider.logger.debug(
                f"Item saved to database: {bus_data.title} (ID: {bus_table.id})"
            )

        except IntegrityError as e:
            session.rollback()
            spider.logger.warning(
                f"Integrity error for item: {bus_data.title if hasattr(bus_data, 'title') else 'Item'} - {e}"
            )

        except Exception as e:
            session.rollback()
            spider.logger.error(
                f"Error processing item: {bus_data.title if hasattr(bus_data, 'title') else 'Item'} - {e}"
            )

        finally:
            session.close()

        return item
