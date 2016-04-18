import os, shutil, sys, json

datafile = os.path.normpath(sys.argv[-1])

if not os.path.exists(datafile) or not os.path.splitext(datafile)[-1] == '.json':
    print ('Wrond data file')
    sys.exit()
try:
    sdata = json.load(open(datafile))
except:
    print ('Error read data file')
    sys.exit()
if sdata['finished']:
    todelete = os.path.dirname(datafile)
    try:
        shutil.rmtree(todelete)
    except:
        print ('Error remove folder %s' % todelete)
        sys.exit()

