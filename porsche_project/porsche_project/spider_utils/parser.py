
import json 

from pathlib import Path 
import sys 

base_dir = Path(__file__).resolve().parents[3]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from utils.logger import log 

def extract_car_object(data) :
    data = json.loads(data)

    items = data.get('@graph') or {}
    if not items:
        return {}
    
    for index, item in enumerate(items, start=0):
        if item['@type'] == ['Product', 'Car']:
            return items[index]


def parse_car_obj(obj: dict):
    odometer = obj.get('mileageFromOdometer') or {}
    offers = obj.get('offers') or {}
    seller = offers.get('seller') or {}
    address = seller.get('address') or {}

    return {
        'vin': obj.get('vehicleIdentificationNumber', None),
        'url': obj.get('url', None),
        'model': obj.get('model', None),
        'inner_color': obj.get('vehicleInteriorColor', None),
        'outer_color': obj.get('color', None),
        'model_date': obj.get('modelDate', None),
        'owners_count': obj.get('numberOfPreviousOwners', None),
        'price': offers.get('price', None),
        'mileage': odometer.get('value', None),
        'dealer': seller.get('name', None),
        'city': address.get('addressLocality', None),
        'postal_code': address.get('postalCode', None),
        'street': address.get('streetAddress', None),
        
    }

