from PySide.QtCore import *
from PySide.QtGui import *
import os, math, sys, argparse

import PySide
lib = os.path.join(os.path.dirname(PySide.__file__), 'plugins')

result_message = 'RESULT::'
error_message = 'ERROR::'
warning_message = 'WARNING::'


# app=QApplication([])
# files = sys.argv[1:]
def main(files, out_image):
    w,h = get_max_size(files)
    mx = brick_matrix(len(files))
    fw = mx[0]*w
    fh = mx[1]*h
    pix = QPixmap(fw, fh)
    p = QPainter()
    p.begin(pix)
    for j in range(mx[0]):
        if not files:break
        for i in range(mx[1]):
            if not files:break
            f = files.pop(0)
            x = w*i
            y = h*j
            p.drawPixmap(x, y, QPixmap(f))
    if os.path.exists(out_image):
        os.remove(out_image)
    pix.save(out_image, 'PNG')
    return out_image

def get_max_size(files):
    x = 0
    y = 0
    for f in files:
        pix = QImage(f)
        x = max([x, pix.width()])
        y = max([y, pix.height()])
    return x, y


def brick_matrix(x):
    c = int(math.ceil(math.sqrt(x)))
    r = (x/c)
    if x%c:
        r +=1
    return int(c), int(r)

def bricker_getMatrix(x, col=None):
    if not col:
        col = int(math.ceil(math.sqrt(x)))
    r = (x/col)
    if x%col:
        r +=1
    return int(col), int(r)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Join many image files together')
    parser.add_argument('-o', '--output',
                        help='Output image')
    parser.add_argument('-f', '--file',
                        nargs='*',
                        help='Input images or folders')
    args = parser.parse_args()
    if not args.output:
        print(error_message+'Output image not set')
        sys.exit(1)
    input_files = []
    skip = []
    for f in args.file:
        if os.path.isfile(f):
            input_files.append(f.replace('\\','/'))
        elif os.path.isdir(f):
            input_files += [os.path.join(f, x).replace('\\','/') for x in os.listdir(f)]
        else:
            skip.append(f)
    if skip:
        print (warning_message+'Error paths: '+' '.join(skip))
    if not input_files:
        print(error_message+'No input files')
        sys.exit(1)

    app = QApplication([])
    app.addLibraryPath(lib)
    img = main(input_files, args.output)
    print (result_message+img+'||')
