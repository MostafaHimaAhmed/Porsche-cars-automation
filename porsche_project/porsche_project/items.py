# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass
from dataclasses import field

@dataclass
class PorscheProjectItem:
    search_name: str = field(default_factory=str )
    vin: str = field(default_factory=str)
    url: str = field(default_factory=str)
    model: str = field(default_factory=str)
    inner_color: str = field(default_factory=str)
    outer_color: str = field(default_factory=str)
    model_date: str = field(default_factory=str)
    owners_count: str = field(default_factory=str)
    price: str = field(default_factory=str)
    mileage: str = field(default_factory=str)
    dealer: str = field(default_factory=str)
    city: str = field(default_factory=str)
    postal_code: str = field(default_factory=str)
    street: str = field(default_factory=str)
    file_urls: list[str] = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    files: list[dict] = field(default_factory=list)
    sticker_downloaded: bool = field(default_factory=bool)
    # options: dict = field(default_factory=dict)
    # total_options: int = field(default_factory=int)
    sticker_path: str = field(default_factory=str)
    first_seen : str = field(default_factory=str)
    last_seen : str = field(default_factory=str)
    body: bytes = field(default_factory=bytes)





