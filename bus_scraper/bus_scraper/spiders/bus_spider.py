import re

import scrapy

from scrapy.utils.response import response_status_message
from scrapy.loader import ItemLoader

from bus_scraper.items import BusesImageItem, BusItem, BusesOverviewItem


"""
Scrapy spider for scraping bus listings from absolutebus.com.

This spider extracts bus details from the listings page and details page. It follows these steps:

1. Extracts basic information from the listings page, including title, source URL, and a flag indicating if the bus is sold.
2. Follows links to individual bus detail pages for further information.
3. Extracts details like images, descriptions, price, air conditioning availability, passenger capacity, mileage, engine/transmission details, gross weight, wheelchair accessibility, and luggage compartments.
4. Builds a dictionary containing bus overview information and assigns it to the scraped item.

It utilizes helper functions for extracting specific data and leverages Scrapy's built-in features for error handling and request following.
"""


class BusSpider(scrapy.Spider):
    """
    Scrapy spider specifically designed for extracting bus listings from absolutebus.com.

    Attributes:
        name (str): The name of the spider (used for identification within Scrapy).
        allowed_domains (list): A list of allowed domains for crawling (prevents crawling outside absolutebus.com).
        start_urls (list): A list of starting URLs for the spider (initial crawl points).
        PASSANGER_KEY (str): Keyword used to identify passenger capacity information (case-insensitive).
        MILES_KEY (str): Keyword used to identify mileage information (case-insensitive).
        WHEELCHAIR_KEY (str): Keyword used to identify wheelchair accessibility information (case-insensitive).
        LUGGAGE_KEY (str): Keyword used to identify luggage compartment information (case-insensitive).
    """

    name = "bus_spider"
    allowed_domains = ["absolutebus.com"]
    start_urls = ["http://absolutebus.com/listings/"]

    PASSANGER_KEY = "psssanger"
    MILES_KEY = "miles"
    WHEELCHAIR_KEY = "wheelchair"
    LUGGAGE_KEY = "luggage"

    def parse(self, response):
        """
        Parses the listings page and extracts basic bus information.

        Iterates through each table element representing a bus listing and extracts data
        like title, source URL, and a flag indicating if the bus is sold. It then follows
        links to individual bus detail pages for further information.

        Args:
            response (scrapy.http.Response): The Scrapy response object for the listings page.

        Yields:
            scrapy.Request: A request object to follow the detail page URL of a bus listing.
        """

        for table in response.css("table"):
            item = BusItem()
            item["source"] = self.allowed_domains[0].split(".")[0]

            title_element = table.css("td:nth-child(2) font:nth-child(1) a")
            title_element_text = title_element.css("::text").get()

            item["title"] = title_element_text.strip() if title_element_text else None

            item["sold"] = is_bus_sold(table)

            bus_url_text = table.css("td:nth-child(1) a::attr(href)").get()

            # Follow the detail page URL
            if bus_url_text:
                full_url = response.urljoin(bus_url_text.strip())
                item["source_url"] = full_url
                yield response.follow(
                    full_url, callback=self.parse_bus_details, meta={"item": item}
                )

        # Check for failed request and log message
        if response.status > 400:
            self.logger.error(
                f"Request failed with status: {response.status} - {response_status_message(response.status)}"
            )

    def parse_bus_details(self, response):
        """
        Parses the bus detail page and extracts detailed bus information.

        Extracts information like images, descriptions, price, air conditioning availability,
        passenger capacity, mileage, engine/transmission details, gross weight, wheelchair accessibility,
        and luggage compartments. It builds a dictionary containing bus overview information
        and assigns it to the scraped item.

        Args:
            response (scrapy.http.Response): The Scrapy response object for the bus detail page.

        Yields:
            dict: A dictionary containing the scraped bus data.
        """

        item = response.meta["item"]  # Access the item dictionary from meta
        item["images"] = []  # Initialize the images dictionary
        overview_info = {}

        # Extract images using the helper function
        main_floor_images_sel = (
            "#bodytext > img:first-child, p.style5 > img, p.style4 > img"
        )
        item["images"].extend(
            extract_images(response, main_floor_images_sel, "main_images")
        )
        item["images"].extend(
            extract_images(response, ".thumbnails a img", "thumbnails")
        )

        body_text = response.css("#bodytext")

        # Get all p tags without classes
        paragraphs_without_class = body_text.css("p:not([class])::text").getall()
        # Clean and strip whitespaces from each paragraph
        paragraphs_cleaned = [p.strip() for p in paragraphs_without_class]

        description_text = "".join(paragraphs_cleaned)
        item["description"] = description_text

        price_text = response.css("h3::text").get()
        item["price"] = extract_price(price_text)

        table = response.css("table.posttable:first-of-type")
        table_rows = table.css("tr")

        item["airconditioning"] = extract_air_conditioning(table_rows)

        other_details = []
        for row in table_rows:
            td = row.css("td")
            text_to_save = extract_text_from_td(td)

            if text_to_save:
                if find_year_make_model(text_to_save, item):
                    continue  # if the year make model is found we continue to the next row
                elif self.PASSANGER_KEY in text_to_save.lower():
                    item["passengers"] = text_to_save
                elif self.MILES_KEY in text_to_save.lower():
                    if item.get("mileage", None):
                        continue
                    item["mileage"] = text_to_save.split(self.MILES_KEY)[0]
                elif any(extract_engine_transmission(text_to_save, item)):
                    continue
                elif extract_gross_weight(text_to_save, item):
                    continue
                elif self.WHEELCHAIR_KEY in text_to_save.lower():
                    item["wheelchair"] = text_to_save
                elif self.LUGGAGE_KEY in text_to_save.lower():
                    item[self.LUGGAGE_KEY] = 1

                else:
                    other_details.append(text_to_save)

        overview_info["features"] = ", ".join(other_details) if other_details else None

        item["bus_overview"] = extract_bus_overview_info(overview_info)

        # Check for failed request and log message
        if response.status > 400:
            self.logger.error(
                f"Request failed with status: {response.status} - {response_status_message(response.status)}"
            )

        yield item


def extract_bus_overview_info(overview_info):
    """Extracts bus overview info."""
    bus_overview_item = BusesOverviewItem()
    bus_overview_item["features"] = overview_info.get("features", None)

    return bus_overview_item


def extract_price(text):
    """Extracts price information from a text string."""
    if not text:
        return None

    price_match = re.search(r"\$([\d,]+(?:\.\d+)?)", text)  # improved regex
    if price_match:
        price = price_match.group(1)
        return price  # return float number
    elif re.search(r"starting at \$([\d,]+(?:\.\d+)?)", text):
        price_match_starting = re.search(r"starting at \$([\d,]+(?:\.\d+)?)", text)
        if price_match_starting:
            price_starting = price_match_starting.group(1)
            return price_starting
    return None


def extract_gross_weight(text, item):
    """Extracts gross weight from a text string."""

    weight_match = re.search(r"Gross weight\s*([\d,]+)#?", text, re.IGNORECASE)
    if weight_match:
        item["gvwr"] = weight_match.group(1).replace(",", "")  # Remove commas
        return True
    return False


def extract_images(response, selector, image_type):
    """Extracts images of a specific type."""
    images = []
    for i, img in enumerate(response.css(selector)):
        image_item = BusesImageItem()  # Create item instance directly

        name_extracted = img.xpath("./@alt").get()
        url_extracted = response.urljoin(img.xpath("./@src").get())
        description_extracted = img.xpath("./@title").get()

        # Assign values like a dictionary, converting to string where needed
        image_item["name"] = name_extracted
        image_item["url"] = url_extracted
        image_item["description"] = description_extracted

        if image_type == "thumbnails":
            image_item["image_index"] = -1 - i
        elif image_type == "main_images":
            image_item["image_index"] = 1 + i
        else:
            image_item["image_index"] = i

        if not image_item.get("name"):
            image_item["name"] = f"{image_type}_{i}"

        images.append(image_item)
    return images


def find_year_make_model(text, item):
    """Extracts year, make, and model from a text string."""
    if find_year_with_space(text):
        parts = [part.strip() for part in text.split(",")]
        if len(parts) >= 2:  # Ensure at least year/make and model are present
            try:
                year = parts[0].split()[0]
                item["year"] = year
                item["make"] = " ".join(parts[0].split()[1:])
                item["model"] = parts[1].strip()
                return True  # return true if the year make model is found
            except (ValueError, IndexError):
                return False
    return False  # return false if the year make model is not found


def find_year_with_space(text):
    """
    Finds a year (4 digits) followed by a space in a given text.

    Args:
        text: The input string to search.

    Returns:
        A match object if found, None otherwise.
    """
    pattern = r"\b(19|20)\d{2}\s\b"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_text_from_td(td_element):
    """
    Extracts text from a table cell, prioritizing strong text and style2 text.

    Args:
        td_element: A Scrapy selector object representing a table cell.

    Returns:
        A string containing the extracted text, combining strong text and regular text.
    """

    text_parts = td_element.css("::text").getall()
    strong_text = td_element.css("strong::text").get()
    style2_text = td_element.css("span.style2::text").get()

    if strong_text:
        return f"{strong_text}, {''.join(text_parts[1:]).strip()}"
    elif style2_text:
        return style2_text.strip()
    else:
        return "".join(text_parts).strip()


def is_bus_sold(table):
    """
    Determines if a bus is sold based on given item data.

    Args:
        item (dict): A dictionary containing bus information, including:
            - price: The price of the bus.
            - sold_out: A boolean indicating if the bus is sold out.

    Returns:
        int: 1 if the bus is sold, 0 otherwise.
    """
    # Check for sold-out status
    sold_out_indicator = "Sold"

    # We can add more conditions here, such as:
    # - Checking if the price is 0 or a specific "Sold Out" string.
    # - Checking for specific keywords in the description.
    if sold_out_indicator in "".join(table.css("::text").getall()):
        return 1
    else:
        return 0


def extract_air_conditioning(rows):
    air_conditioning_text = None

    for row in rows:
        text = extract_text_from_td(row.css("td"))
        if re.search(
            r"(?:A/C|AC|Air conditioning|BTU)", text, re.IGNORECASE
        ):  # check if contains AC or BTU
            air_conditioning_text = text
            break  # Stop after finding the first match

    if not air_conditioning_text:
        return None  # default value

    # Check for "front and rear" FIRST
    if re.search(r"front and rear", text, re.IGNORECASE):
        if re.search(
            r"dual compressor", text, re.IGNORECASE
        ):  # check if also has dual compressor
            return "BOTH"
        return "BOTH"

    # Then check for "dual compressor" (in any order with "front and rear")
    elif re.search(r"(?:front and rear|dual)\s*dual compressor", text, re.IGNORECASE):
        return "BOTH"
    elif re.search(r"dual compressor\s*(?:front and rear)", text, re.IGNORECASE):
        return "BOTH"
    elif re.search(r"rear", text, re.IGNORECASE):
        return "REAR"
    elif re.search(r"dash", text, re.IGNORECASE):
        return "DASH"
    else:
        return "OTHER"


def extract_engine(text):
    """Extracts engine information from a text string."""
    # Engine extraction (prioritize known school bus engines)
    engine_match = re.search(
        r"(DT\d{3} [^,]+\s*diesel)|(Duramax [^,]+\s*diesel)|(Ecoboost [^,]+\s*gas)",
        text,
        re.IGNORECASE,
    )
    if engine_match:
        return engine_match.group(1).strip()
    else:
        # Fallback for other engines
        engine_match = re.search(
            r"([\d.]+[a-zA-Z\d\s]+(?:diesel|gas|engine|V\d+)+)", text, re.IGNORECASE
        )
        if engine_match:
            return engine_match.group(1).strip()
    return None


def extract_transmission(text):
    """Extracts transmission information from a text string."""
    if not text:
        return None

    # Prioritized regex
    transmission_match = re.search(
        r"(Allison|10\s*speed|(?:\d+\s*(?:spd|speed))\s*(?:ovrdrv|overdrive)?\s*(?:auto|automatic)?)",
        text,
        re.IGNORECASE,
    )
    if transmission_match:
        return transmission_match.group(1).strip()

    # Fallback regex
    transmission_match = re.search(
        r"(\d+\s*spd|speed|automatic|trans|ovrdrv|overdrive)", text, re.IGNORECASE
    )
    if transmission_match:
        return transmission_match.group(1).strip()

    return None


def extract_engine_transmission(text, item):
    """Extracts engine and transmission information from school bus text."""

    engine = None
    transmission = None

    # Engine extraction (prioritize known school bus engines)
    engine_match = re.search(
        r"(DT\d{3} [^,]+\s*diesel)|(Duramax [^,]+\s*diesel)|(Ecoboost [^,]+\s*gas)",
        text,
        re.IGNORECASE,
    )
    if engine_match:
        engine = engine_match.group(1).strip()
    else:
        # Fallback for other engines
        engine_match = re.search(
            r"([\d.]+[a-zA-Z\d\s]+(?:diesel|gas|engine|V\d+)+)", text, re.IGNORECASE
        )
        if engine_match:
            engine = engine_match.group(1).strip()

    transmission = extract_transmission(text)

    item["engine"] = engine if not item.get("engine", None) else item["engine"]
    item["transmission"] = (
        transmission if not item.get("transmission", None) else item["transmission"]
    )

    return engine, transmission
