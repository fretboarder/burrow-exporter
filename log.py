import logging, json

def init_logging(default_level='INFO'):
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=getattr(logging, default_level.upper()))

def logI(s): logging.info('{}'.format(s))

def logD(s): logging.debug('{}'.format(s))

def logW(s): logging.warning('{}'.format(s))

def jdump(o):
    for l in json.dumps(o, indent=2).split('\n'):
        logD(l)