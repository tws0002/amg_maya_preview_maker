from PySide.QtCore import *
from PySide.QtGui import *
import os, sys, json, re, glob

import PySide
pyside_root = os.path.dirname(PySide.__file__)
path = os.path.join(pyside_root, 'plugins').replace('\\','/')


default_font_size = 20
default_bg_color = (0,0,0,130,)
default_backdrop_color = (0,0,0,255,)
padding = 20



def get_logo():
    if __name__ == '__builtin__':
        return r'D:\Dropbox\Dropbox\pw_pipeline\pw_pipeline\assets\maya\python\TOOLS\asset_submitter\lib\logo.png'
    logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib/logo.png')
    if os.path.exists(logo):
        return logo.replace('\\','/')

def get_font(path=None, size=20, filepath=False):
    # if __name__ == '__builtin__':
    #     path = r'D:\Dropbox\Dropbox\pw_pipeline\pw_pipeline\assets\maya\python\TOOLS\asset_submitter\lib\LUCON.TTF'
    if not path or not os.path.exists(path):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib/LUCON.TTF').replace('\\','/')
    if filepath:
        return path
    id = QFontDatabase.addApplicationFont(path)
    family = QFontDatabase.applicationFontFamilies(id)[0]
    return QFont(family, size)


def default_image(w=640, h=480, checkersize=80, asQt=False):
    img = QPixmap(w, h)
    ch = checkersize
    draw = QPainter()
    draw.begin(img)
    draw.setRenderHint(QPainter.HighQualityAntialiasing, True)
    draw.fillRect(img.rect(), QBrush(QColor('white')))
    count_x = ((w-(w%ch))/ch)+1
    count_y = ((h-(h%ch))/ch)+2
    draw.setBrush(QBrush(QColor(200,200,200)))
    draw.setPen(QPen(QColor('black'), 4))
    for y in range(0, count_y):
        for x in range(0, count_x, 2):
            a = ch*(y%2)
            rec = QRect((ch*x)+a,(ch*y), ch, ch)
            draw.fillRect(rec, QBrush(QColor(200,200,200)))
    return img

def add_stamp( data, image_path=None, raw_image = None, out_image=None, font_size=default_font_size,
               font=None, test=False, bg_color=None, logo=True, qtpixmap=False,
               backdrop=False, backdrop_bg=None):
    drawfont = get_font(font, size=font_size)
    fm = QFontMetrics (drawfont)
    bg_color = bg_color or default_bg_color
    backdrop_bg = backdrop_bg or (bg_color[0],bg_color[1],bg_color[2],bg_color[3]+((255-bg_color[3])/2) )

    # lines
    max_lines_t = max([len(x) for k, x in data.items() if k[0] == 't'] or [0])
    max_lines_b = max([len(x) for k, x in data.items() if k[0] == 'b'] or [0])
    line_height = int(fm.height()*1.3)
    subline = line_height - font_size

    # load image
    if image_path:
        source = QPixmap(image_path)
        if source.isNull():
            print ('Error load Image', image_path)
            return
    elif raw_image:
        source = raw_image
    else:
        raise Exception('Source image not set')
    draw = QPainter()
    draw.begin(source)
    draw.setFont(drawfont)

    # frame
    rect_height_t = (line_height*max_lines_t) + subline
    rect_height_b = (line_height*max_lines_b) + subline
    size = (source.size().width(), source.size().height())
    if max_lines_t:
        rect_t = (0,0,size[0], rect_height_t)
    else:
        rect_t = None
    if max_lines_b:
        rect_b = (0, size[1]-rect_height_b, size[0], size[1])
    else:
        rect_b = None
    for rect in [x for x in (rect_t, rect_b) if x]:
       draw.fillRect(rect[0],rect[1],rect[2],rect[3], QColor(*bg_color))

    # logo
    if logo:
        if not (isinstance(logo, str) and os.path.exists(logo)):
            logo = get_logo()
        if logo:
            logoimg = QPixmap(get_logo())
            logoimg = logoimg.scaled(QSize(source.size().width(),rect_height_t-subline), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            draw.drawPixmap(QPoint(source.size().width()-subline-logoimg.size().width(),subline/2), logoimg)
        else:
            w, h = 500,500
            width = 30
            logoimg = QImage(w,h, QImage.Format_ARGB32_Premultiplied)
            logoimg.fill(Qt.transparent)
            p = QPainter(logoimg)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor('red'), width))
            p.drawLine(0,0, w,h)
            p.drawLine(w,0, 0,h)
            p.end()
            logoimg = logoimg.scaled(size[0],rect_height_t-subline, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            draw.drawImage(QPoint(source.size().width()-subline-logoimg.size().width(),subline/2), logoimg)

    # text
    offset = max([max([len(z[0]) for z in x] or [0]) for x in data.values()] or [0])
    center = max([max([len(z[1]) for z in x] or [0]) for x in data.values()] or [0])

    bottom_offset = size[1]-rect_height_b
    for pos, lines in data.items():
        if not lines:
            continue
        blockLines = []
        leftMax = max([len(x[1]) for x in lines])

        for line in lines:
            if line[0]:
                blockLines.append("{0:>{offset}} : {1:<{center}}".format(line[0],line[1], offset=offset, center=leftMax))
            else:
                blockLines.append(line[1].center(center))

        maxtextwidth = max([fm.width(x.replace(' ','_')) for x in blockLines])

        for i, l in enumerate(blockLines):
            linepos = subline + ((subline+font_size)*i)
            to_center = (line_height*((max_lines_t if pos[0] == 't' else max_lines_b) - len(blockLines)))/2
            sz = fm.width(l.replace(' ','_')), fm.height()
            blockOffset = [0,0]
            # top
            if pos == 'tl':
                blockOffset = [padding,to_center]
            elif pos == 'tm':
                blockOffset = [(size[0]/2) - (maxtextwidth/2),to_center]
            elif pos == 'tr':
                blockOffset = [size[0]-padding-maxtextwidth, to_center]
            # bottom
            elif pos == 'bl':
                blockOffset = [padding,bottom_offset+to_center]
            elif pos == 'bm':
                blockOffset = [(size[0]/2) - (maxtextwidth/2), bottom_offset+to_center]
            elif pos == 'br':
                blockOffset = [size[0]-maxtextwidth-padding, bottom_offset+to_center]
            text_point = QPoint(blockOffset[0], linepos+blockOffset[1]+(line_height/2))
            if backdrop and l.strip():
                backdrop_offset = 4
                r = (
                     blockOffset[0]-backdrop_offset ,
                     blockOffset[1]+sz[1]+linepos-line_height+(subline/4)-backdrop_offset ,
                     sz[0]+(backdrop_offset*2),
                     sz[1]+backdrop_offset
                    )
                draw.fillRect(QRect(*r), QColor(*backdrop_bg))
            draw.setPen(QPen(QColor(255,255,255)))
            draw.drawText(text_point, l)
    draw.end()
    # save
    if qtpixmap:
        return source
    if test:
        path, ext = os.path.splitext(image_path)
        source.save(path+'_test'+ext, 'JPG')
    else:
        source.save(out_image or image_path, 'JPG')


data_example = dict(
    tl=[ # top left
        ['Project',   'Project1'      ],
        ['Artist',    'Username'      ],
        ['Date',      '12.01.2016'    ]
    ],
    tm=[ # top middle
    ],
    tr=[ # top right (logo)
    ],
    bl=[ # bottom left
        ['Sequence',  'EP0111'         ],
        ['Shot',      'sh0011',       ],
        ['Step',      'FX',           ],
        ['Task',      'dust-sim',     ],
    ],
    bm=[ # bottom middle
        ['',          'EP029sh-0030', ],
        ['',          'v005'          ],
    ],
    br=[ # bottom right
        ['Frame',     '{frame:4}'          ]
    ]
)

# Example use


jsonExample = '''
{
    "":"STAMP DATA",
    "stamp": {
        "":"top left",
        "tl": [
            ["Project","Project1"],
            ["Artist","Username"],
            ["Date", "12.01.2016"]
        ],
        "":"top middle",
        "tm": [],
        "":"top right",
        "tr": [],
        "":"bottom left",
        "bl": [
            ["Sequence", "EP029"],
            ["Shot","sh0030"],
            ["Step", "FX"],
            ["Task","dust-sim"]
        ],
        "":"bottom muddle",
        "bm": [
            ["","EP029sh-0030"],
            ["","v005"]
        ],
        "":"bottom right",
        "br": [
            ["Frame","{frame:4}"]
        ]
    },
    "bg_color": [0,0,0,180],
    "font": "path/to/font/file.ttf",
    "font_size": 14,
    "test": false,
    "logo": true,
    "backdrop":true,

    "":"RENDER DATA" ,
    "resolution":[640, 460],
    "engine":"ai",
        "":" 'ai' - arnold, 'blast' - Maya playblast, 'hw' - Maya hardware",
    "layer":"",
    "range":[0,100],
    "outfilename":"filename",

    "":"FILES DATA",
    "tmpdir":"",
    "mayascene":"path",
    "jpgfiles":[],

    "":"FFMPEG DATA",
    "movfile":"path"
}
'''

def set_frame_number(data, num):
    if isinstance(data, dict):
        for k, v in data.items():
            d = set_frame_number(v, num)
            if d:
                return data
    elif isinstance(data, list):
        for v in data:
            try:
                isstring = isinstance(v, (str, unicode))
            except:
                isstring = isinstance(v, str)
            if isstring:
                find = re.findall(r"^\{frame:(\d+)\}$", v)
                if find:
                    nv = str(num).zfill(int(find[0]))
                    i = data.index(v)
                    data.remove(v)
                    data.insert(i,nv)
                    return data
            # else:
            d = set_frame_number(v, num)
            if d:
                return data
    # return data

def main():
    """
    input file
    output file
    data_file.json
    """
    if not sys.argv[1:]:
        print ('Arguments not set')
        exit()
    datafile = sys.argv[-1]
    data = json.load(open(datafile))
    for folder in data['jpgfiles']:
        if os.path.isdir(folder):
            for i, image in enumerate(glob.glob1(folder, '*.jpg')):
                # for i, image in enumerate(data['jpgfiles']):
                image = os.path.join(folder,image).replace('\\','/')
                stamp = data['stamp']
                f = re.findall(r"(\d+)\.\w+$", image)
                if f:
                    frame = f[0]
                else:
                    frame = i
                stamp = set_frame_number(stamp, frame) or stamp
                add_stamp(stamp['stamp'],
                          image,
                          font_size=data.get('font_size', default_font_size),
                          bg_color=data.get('bg_color', default_bg_color),
                          logo=data.get('logo', True),
                          font=data.get('font')
                          )
                print (i)
    sys.exit()

if __name__ == '__main__':
    if not QCoreApplication.instance():
        app = QApplication([])
        app.addLibraryPath(path)
        main()
        # app.exec_()
    else:
        main()



