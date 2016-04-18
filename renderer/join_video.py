import os, sys, argparse, tempfile, re

amg = os.getenv('AMG_ROOT') or 'D:/work/amg/amg_pipeline'
ffmpeg = os.path.join(amg, 'cgru', 'bin', 'ffmpeg')

result_message = 'RESULT::'
error_message = 'ERROR::'
warning_message = 'WARNING::'


def main(input_files, out_file):
    tmp = os.path.join(tempfile.gettempdir(), 'joinvideos.txt')
    text = ' '.join(["file '%s'\n" % x for x in input_files])
    open(tmp, 'w').write(text.strip())

    cmd = '{ffmpeg} -f concat -i {input} -c copy {output}'.format(
        ffmpeg=ffmpeg,
        input=tmp,
        output=out_file
    )
    os.system(cmd)
    os.remove(tmp)
    return out_file

def incrementSaveName(path, padding=3):
    bname = os.path.basename(path)
    dname = os.path.dirname(path)
    name, ext = os.path.splitext(bname)
    r = re.match(r"(.*?)(\d+)$", name)
    if r:
        n, d = r.groups()
        name = n + str(int(d)+1).zfill(len(d))
        result = os.path.join(dname, name+ext).replace('\\','/')
    else:
        result = os.path.join(dname, name+ '_%s' % str(1).zfill(padding)+ext).replace('\\','/')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='... saves many files together...')
    parser.add_argument('-o', '--output',
                        help='Output video')
    parser.add_argument('-f', '--file',
                        nargs='*',
                        help='Input video files')
    args = parser.parse_args()
    if not args.output:
        print(error_message+'Output file not set')
        sys.exit(1)
    input_files = []
    skip = []
    for f in args.file:
        if os.path.isfile(f):
            input_files.append(f.replace('\\','/'))
        else:
            skip.append(f)
    if skip:
        print (warning_message+'Error paths: '+' '.join(skip))
    if not input_files:
        print(error_message+'No input files')
        sys.exit(1)
    out = args.output
    if os.path.exists(out):
        os.remove(out)
    # while os.path.exists(out):
    #     out = incrementSaveName(out)
    img = main(input_files, out)
    print (result_message+out+'||')