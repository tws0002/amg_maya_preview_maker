from PIL import  Image, ImageDraw, ImageFont
import os, sys, json
from PySide.QtGui import QImage, QPixmap

default_font_size = 20
default_bg_color = (0,0,0, 180)
default_backdrop_color = (0,0,0, 255)
padding = 20



def get_logo():
    if __name__ == '__builtin__':
        return r'D:\Dropbox\Dropbox\pw_pipeline\pw_pipeline\assets\maya\python\TOOLS\asset_submitter\lib\logo.png'
    logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib/logo.png')
    if os.path.exists(logo):
        return logo.replace('\\','/')

def get_font():
    if __name__ == '__builtin__':
        return r'D:\Dropbox\Dropbox\pw_pipeline\pw_pipeline\assets\maya\python\TOOLS\asset_submitter\lib\LUCON.TTF'
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib/LUCON.TTF')

def pil_to_pixmap(img):
    im_rgb = img.convert('RGBA')
    r, g, b, a = im_rgb.split()
    im_rgb = Image.merge('RGBA', (b, g, r, a))
    data = im_rgb.tobytes('raw', 'RGBA')
    image = QImage(data, img.size[0], img.size[1], QImage.Format_ARGB32 )
    pix = QPixmap(image)
    return pix

def default_image(w=640, h=480, checkersize=80, asQt=False):
    img = Image.new("RGB", (w,h), (255,255,255))
    ch = checkersize
    draw = ImageDraw.Draw(img)
    count_x = ((w-img.size[0]%ch)/ch)+1
    count_y = ((h-img.size[0]%ch)/ch)+2

    for y in range(0, count_y):
        for x in range(0, count_x, 2):
            a = ch*(y%2)
            rec = ((ch*x)+a,
                   (ch*y),
                  (ch*x)+ch+a,
                  (ch*y)+ch)
            draw.rectangle(rec, fill=(200,200,200))
    return img

def add_stamp( data, image_path=None, raw_image = None, out_image=None, font_size=default_font_size,
               font=None, test=False, bg_color=default_bg_color, logo=True, qtpixmap=False,
               backdrop=False, backdrop_bg=None):
    font = font or get_font()
    backdrop_bg = backdrop_bg or (bg_color[0],bg_color[1],bg_color[2],bg_color[3]+((255-bg_color[3])/2) )
    if not os.path.exists(font):
        raise Exception('Font Not found')



    # lines
    max_lines_t = max([len(x) for k, x in data.items() if k[0] == 't'] or [0])
    max_lines_b = max([len(x) for k, x in data.items() if k[0] == 'b'] or [0])
    line_height = int(font_size*1.3)
    subline = line_height - font_size

    # load image
    if image_path:
        source = Image.open(image_path)
    elif raw_image:
        source = raw_image
    else:
        raise Exception('Source image not set')
    draw = ImageDraw.Draw(source, 'RGBA')
    drawfont = ImageFont.truetype(font, font_size)

    # frame
    rect_height_t = (line_height*max_lines_t) + subline
    rect_height_b = (line_height*max_lines_b) + subline

    if max_lines_t:
        rect_t = (0,0,source.size[0], rect_height_t)
    else:
        rect_t = None
    if max_lines_b:
        rect_b = (0, source.size[1]-rect_height_b, source.size[0], source.size[1])
    else:
        rect_b = None
    for rect in [x for x in rect_t, rect_b if x]:
       draw.rectangle(rect, fill=tuple(bg_color))

    # logo
    if logo:
        if not (isinstance(logo, str) and os.path.exists(logo)):
            logo = get_logo()
        if logo:
            logoimg = Image.open(get_logo())
            logoimg.thumbnail((source.size[0],rect_height_t-subline), Image.ANTIALIAS)
            source.paste(logoimg,(source.size[0]-subline-logoimg.size[0],subline/2), mask=logoimg)
        else:
            w, h = 500,500
            width = 30
            logoimg = Image.new("RGB", (w,h), (0,0,0))
            cdraw = ImageDraw.Draw(logoimg)
            cdraw.line((0,0, w,h), fill=(255,0,0), width=width)
            cdraw.line((w,0, 0,h), fill=(255,0,0), width=width)
            logoimg.thumbnail((source.size[0],rect_height_t-subline), Image.ANTIALIAS)
            source.paste(logoimg,(source.size[0]-subline-logoimg.size[0],subline/2))

    # text
    offset = max([max([len(z[0]) for z in x] or [0]) for x in data.values()] or [0])
    center = max([max([len(z[1]) for z in x] or [0]) for x in data.values()] or [0])

    bottom_offset = source.size[1]-rect_height_b
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
        maxtextwidth = max([draw.textsize(x.replace(' ','_'), drawfont)[0] for x in blockLines])
        for i, l in enumerate(blockLines):
            linepos = subline + ((subline+font_size)*i)
            to_center = (line_height*((max_lines_t if pos[0] == 't' else max_lines_b) - len(blockLines)))/2

            blockOffset = [0,0]
            # top
            if pos == 'tl':
                blockOffset = [padding,to_center]
            elif pos == 'tm':
                blockOffset = [(source.size[0]/2) - (maxtextwidth/2),to_center]
            elif pos == 'tr':
                blockOffset = [source.size[0]-padding-maxtextwidth, to_center]
            # bottom
            elif pos == 'bl':
                blockOffset = [padding,bottom_offset+to_center]
            elif pos == 'bm':
                blockOffset = [(source.size[0]/2) - (maxtextwidth/2), bottom_offset+to_center]
            elif pos == 'br':
                blockOffset = [source.size[0]-maxtextwidth-padding, bottom_offset+to_center]
            if backdrop:
                backdrop_offset = 1#(subline/3)
                sz = draw.textsize(l.replace(' ','_'), drawfont)
                r = (blockOffset[0]-backdrop_offset, linepos+blockOffset[1]-backdrop_offset,
                     blockOffset[0]+sz[0]+backdrop_offset, linepos+blockOffset[1]+sz[1]+backdrop_offset)
                draw.rectangle(r, fill=tuple(backdrop_bg))
            draw.text((blockOffset[0], linepos+blockOffset[1]),l,(255,255,255),font=drawfont)

    # save
    if qtpixmap:
        return pil_to_pixmap(source)
    if test:
        path, ext = os.path.splitext(image_path)
        source.save(path+'_test'+ext)
    else:
        source.save(out_image or image_path)


data_example = dict(
    tl=[ # top left
        ['Project',   'Project1'      ],
        ['Artist',    'Username'      ],
        ['Date',      '12.01.1111'    ]
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
        ['Frame',     '0123'          ]
    ]
)
# Example use
# add_stamp('C:/Shot_template.jpg', data_example, test=True, font_size=20, bg_color=[0,0,0,180])
# i = add_stamp('C:/Shot_template.jpg', data_example, test=True, font_size=20, bg_color=[0,0,0,180], qtimage=1)


jsonExample = '''
{
    "stamp": {
        "bl": [
            ["Sequence", "EP029"],
            ["Shot","sh0030"],
            ["Step", "FX"],
            ["Task","dust-sim"]
        ],
        "bm": [
            ["","EP029sh-0030"],
            ["","v005"]
        ],
        "tr": [],
        "tl": [
            ["Project","Project1"],
            ["Artist","Username"],
            ["Date", "12.01.2016"]
        ],
        "tm": [],
        "br": [
            ["Frame","0127"]
        ]
    },
    "bg_color": [0,0,0,180],
    "font": "path/to/font/file.ttf"
    "font_size": 20,
    "test": false,
    "logo": true,
}
'''

def main():
    """
    input file
    output file
    data_file.json
    """
    if not sys.argv[1:]:
        print 'Arguments not set'
        exit()
    if len(sys.argv) != 4:
        print 'Error arguments number'
        exit()
    image = sys.argv[-3]
    if not os.path.exists(image):
        print 'Image file not found'
        exit()
    out_image = sys.argv[-2]
    datafile = sys.argv[-1]
    datastamp = json.load(open(datafile))
    if not datastamp.get('stamp'):
        print 'Not stamp data'
        exit()
    add_stamp(image,
              datastamp['stamp'],
              out_image,
              test=datastamp.get('test', False),
              font_size=datastamp.get('font_size', default_font_size),
              bg_color=datastamp.get('bg_color', default_bg_color),
              logo=datastamp.get('logo', True),
              font=datastamp.get('font')
              )

if __name__ == '__main__':
    main()



