"""Constants for Moscow Hot Water."""
from datetime import timedelta

DOMAIN = "moscow_hot_water"

CONF_ADDRESS_QUERY = "address_query"
CONF_ADDRESS = "address"
CONF_UNOM = "unom"

DEFAULT_SCAN_INTERVAL = timedelta(hours=12)
SOURCE_URL = "https://www.mos.ru/otvet-dom-i-dvor/grafik-otklucheniya-goryachei-vodi/"
API_URL = "https://www.mos.ru/aisearch/hwsuggest/api/v1/suggest/"
