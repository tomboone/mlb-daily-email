import logging

logging.basicConfig(
    filename='./log/mlb.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
