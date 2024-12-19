# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from typing import Optional, List, Dict, Any

from itemloaders.processors import MapCompose, TakeFirst


def convert_to_string(value):
    """Converts a list or any other value to a string."""
    if isinstance(value, list):
        return value[0] if value else None  # Get the first element or None if empty
    return str(value) if value is not None else None  # convert to string if is not None


def convert_to_int(value):
    """Converts a list or any other value to a int."""
    if isinstance(value, list):
        return value[0] if value else None  # Get the first element or None if empty
    return int(value) if value is not None else None  # convert to int if is not None


class BusesImageItem(Item):
    name: Optional[str] = Field()
    alt_text: Optional[str] = Field()
    url: Optional[str] = Field()
    description: Optional[str] = Field()
    image_index: Optional[int] = Field()
    bus_id: Optional[int] = Field()


class BusItem(Item):
    title = Field()
    year: Optional[str] = Field()
    make: Optional[str] = Field()
    model: Optional[str] = Field()
    body: Optional[str] = Field()
    chassis: Optional[str] = Field()
    engine: Optional[str] = Field()
    transmission: Optional[str] = Field()
    mileage: Optional[str] = Field()
    passengers: Optional[str] = Field()
    wheelchair: Optional[str] = Field()
    color: Optional[str] = Field()
    interior_color: Optional[str] = Field()
    exterior_color: Optional[str] = Field()
    published: Optional[bool] = Field()
    featured: Optional[bool] = Field()
    sold: Optional[bool] = Field()
    scraped: Optional[bool] = True
    draft: Optional[bool] = Field()
    source: Optional[str] = Field()
    source_url: Optional[str] = Field()
    price: Optional[str] = Field()
    cprice: Optional[str] = Field()
    vin: Optional[str] = Field()
    gvwr: Optional[str] = Field()
    dimensions: Optional[str] = Field()
    luggage: Optional[bool] = Field()
    state_bus_standard: Optional[str] = Field()
    airconditioning: Optional[str] = Field()
    location: Optional[str] = Field()
    brake: Optional[str] = Field()
    contact_email: Optional[str] = Field()
    contact_phone: Optional[str] = Field()
    us_region: Optional[str] = Field()
    description: Optional[str] = Field()
    score: Optional[int] = Field()
    category_id: Optional[int] = Field()
    images: Optional[List[Dict[str, Any]]] = Field()
    bus_overview: Optional[Dict[str, Any]] = Field()


class BusesImageItem(Item):
    name: Optional[str] = Field()
    url: Optional[str] = Field()
    description: Optional[str] = Field()
    image_index: Optional[int] = Field()
    bus_id: Optional[int] = Field()


class BusesOverviewItem(Item):
    mdesc: Optional[str] = Field()
    intdesc: Optional[str] = Field()
    extdesc: Optional[str] = Field()
    features: Optional[str] = Field()
    specs: Optional[str] = Field()
    bus_id: Optional[int] = Field()
