import re

from typing import List, Optional

from pydantic import BaseModel, field_validator, ValidationError
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    ForeignKey,
    Enum,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP


from typing import List, Optional
from pydantic import BaseModel


class BusesImage(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    image_index: Optional[int] = 0
    bus_id: Optional[int] = None


class BusesOverview(BaseModel):
    bus_id: Optional[int] = None
    mdesc: Optional[str] = None
    intdesc: Optional[str] = None
    extdesc: Optional[str] = None
    features: Optional[str] = None
    specs: Optional[str] = None


class Bus(BaseModel):
    title: Optional[str] = None
    year: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    body: Optional[str] = None
    chassis: Optional[str] = None
    engine: Optional[str] = None
    transmission: Optional[str] = None
    mileage: Optional[str] = None
    passengers: Optional[str] = None
    wheelchair: Optional[str] = None
    color: Optional[str] = None
    interior_color: Optional[str] = None
    exterior_color: Optional[str] = None
    published: Optional[bool] = False
    featured: Optional[bool] = False
    sold: Optional[bool] = False
    scraped: Optional[bool] = True
    draft: Optional[bool] = False
    source: Optional[str] = None
    source_url: Optional[str] = None
    price: Optional[str] = None
    cprice: Optional[str] = None
    vin: Optional[str] = None
    gvwr: Optional[str] = None
    dimensions: Optional[str] = None
    luggage: Optional[bool] = False
    state_bus_standard: Optional[str] = None
    airconditioning: Optional[str] = None  # Use str for ENUM
    location: Optional[str] = None
    brake: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    us_region: Optional[str] = None  # Use str for ENUM
    description: Optional[str] = None
    score: Optional[int] = 0
    category_id: Optional[int] = 0
    images: Optional[List[BusesImage]] = None
    bus_overview: Optional[BusesOverview] = None

    @field_validator("price")
    def validate_price(cls, v):
        if v is not None:
            v = v.split(".")[0]
            digits_only = re.sub(r"\D", "", v)  # Remove non-digit characters
            if (
                not digits_only
            ):  # check if the string is empty after removing the non digits characters
                return None
            return digits_only
        return v

    @field_validator("year")
    def validate_year(cls, v):
        if v is not None:
            try:
                year = int(v)
                if not (1900 <= year <= 2100):  # Basic year range check
                    raise ValueError("Year must be between 1900 and 2100")
                return str(year)
            except ValueError:
                raise ValueError("Invalid year format")
        return v

    @field_validator("make")
    def validate_make(cls, v):
        if v is not None:
            try:
                return v.split(" ")[0]
            except IndexError:
                raise IndexError("Not valid make")
        return v

    @field_validator("wheelchair")
    def validate_wheelchair(cls, v):
        if v is not None:
            v = v.strip()  # Remove leading/trailing whitespace
            if len(v) > 60:  # Explicit length check
                v = v[:60]  # Truncate to 60 characters
            return v
        return v


Base = declarative_base()


class BusesOverviewTable(Base):
    __tablename__ = "buses_overview"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    mdesc = Column(Text)
    intdesc = Column(Text)
    extdesc = Column(Text)
    features = Column(Text)
    specs = Column(Text)

    # Relationship
    bus = relationship("BusTable", back_populates="overview")


class BusesImageTable(Base):
    __tablename__ = "buses_images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64))
    url = Column(String(1000))
    description = Column(Text)
    image_index = Column(Integer)
    bus_id = Column(Integer, ForeignKey("buses.id"))

    # Relationship
    bus = relationship("BusTable", back_populates="images")


class BusTable(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256))
    year = Column(String(10))
    make = Column(String(25))
    model = Column(String(50))
    body = Column(String(25))
    chassis = Column(String(25))
    engine = Column(String(60))
    transmission = Column(String(60))
    mileage = Column(String(100))
    passengers = Column(String(60))
    wheelchair = Column(String(60))
    color = Column(String(60))
    interior_color = Column(String(60))
    exterior_color = Column(String(60))
    published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    sold = Column(Boolean, default=False)
    scraped = Column(Boolean, default=False)
    draft = Column(Boolean, default=False)
    source = Column(String(300))
    source_url = Column(String(1000))
    price = Column(String(30))
    cprice = Column(String(30))
    vin = Column(String(60))
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, default=func.now())
    gvwr = Column(String(50))
    dimensions = Column(String(300))
    luggage = Column(Boolean, default=False)
    state_bus_standard = Column(String(25))
    airconditioning = Column(Enum("REAR", "DASH", "BOTH", "OTHER", "NONE"))
    location = Column(String(30))
    brake = Column(String(30))
    contact_email = Column(String(100))
    contact_phone = Column(String(100))
    us_region = Column(
        Enum("NORTHEAST", "MIDWEST", "WEST", "SOUTHWEST", "SOUTHEAST", "OTHER")
    )
    description = Column(Text)
    score = Column(Integer, default=0)
    category_id = Column(Integer, default=0)

    # Relationships
    overview = relationship(
        "BusesOverviewTable", back_populates="bus", uselist=False
    )  # One-to-one
    images = relationship("BusesImageTable", back_populates="bus")  # One-to-many
