import os, sys

def init_af(cgrupath):
    CGRU_LOCATION = cgrupath
    os.environ['CGRU_LOCATION']= CGRU_LOCATION
    AF_PYTHON='/'.join([CGRU_LOCATION,'afanasy/python'])
    CGRU_PYTHON='/'.join([CGRU_LOCATION,'lib/python'])
    os.environ['PYTHONPATH']=';'.join([AF_PYTHON, os.environ.get('PYTHONPATH','')])
    os.environ['PYTHONPATH']=';'.join([CGRU_PYTHON, os.environ.get('PYTHONPATH','')])
    sys.path.append(AF_PYTHON)
    sys.path.append(CGRU_PYTHON)
if not os.getenv('CGRU_LOCATION'):
    init_af('D:/Dropbox/Dropbox/pw_pipeline/pw_pipeline/modules/win/cgru')



