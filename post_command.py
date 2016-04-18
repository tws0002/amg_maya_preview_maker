import os, sys, json, subprocess, re, shutil

pyexec = sys.executable
result_message = 'RESULT::'
error_message = 'ERROR::'
warning_message = 'WARNING::'

def join(*args):
    return '/'.join([str(x) for x in args]).replace('\\','/').replace('/','/')

def join_video(files, output):
    rend = os.path.join(os.path.dirname(__file__), 'renderer','join_video.py').replace('/','\\')
    files = ' '.join(files)
    cmd = '{py} {renderer} -f {files} -o {output}'.format(
        py=pyexec,
        renderer=rend,
        files = files,
        output=output
    )
    res = subprocess.check_output(cmd)
    f = re.findall(r"RESULT::(.*?)\|\|", str(res))
    if f:
        path = f[0].strip().replace('\\','/').replace('//','/').replace("'",'').replace('"','')
        return path


def join_images(files, output):
    render = os.path.join(os.path.dirname(__file__), 'renderer','join_images.py').replace('/','\\')
    files = ' '.join(files)
    cmd = '{py} {renderer} -f {files} -o {output}'.format(
        py=pyexec,
        renderer=render,
        files = files,
        output=output
    )
    res = subprocess.check_output(cmd)
    f = re.findall(r"RESULT::(.*?)\|\|", str(res))
    if f:
        path = f[0].strip().replace('\\','/').replace('//','/').replace("'",'').replace('"','')
        return path

def finished(path):
    pass

if __name__ == '__main__':
    # get datafile
    datafile = sys.argv[-1]
    # datafile = 'D:/work/amg/temp/previewer_render_205703/submit_data_205703.json'

    # search result images and videos
    sdata = json.load(open(datafile))
    data_files = [json.load(open(x)) for x in sdata['datafiles']]
    output_files = []
    # defile groups
    groups = {}
    for d in data_files:
        grp = d['group']
        if grp in groups:
            groups[grp].append(d)
        else:
            groups[grp] = [d]
    for g, grp in groups.items():
        join_movies_list = []
        join_images_list = []
        for data in grp:
            # video
            if data['ismove']:
                if data['join_outputs']:
                    join_movies_list += data['outfiles']
                else:
                    output_files += data['outfiles']
            # images
            else:
                if data['join_outputs']:
                    for path in data['jpgfiles']:
                        join_images_list.append({data['id']:sorted(list(set([os.path.join(path,x).replace('\\','/') for x in os.listdir(path)])))})
                else:
                    for path in data['jpgfiles']:
                        output_files += [join(path,x) for x in os.listdir(path)]
        root = os.path.dirname(datafile)
        if join_movies_list:
            out_path = os.path.join(root, 'joined_%s_grp_%s.mp4' % (sdata['id'], g)).replace('/','\\')
            if len(join_movies_list) > 1:
                joinmovies = sorted(list(set([x.replace('/','\\') for x in join_movies_list])))
                # join_name = '_'.join([os.path.splitext(os.path.basename(x))[0].split('_')[-1] for x in joinmovies])

                if os.path.exists(out_path):
                    os.remove(out_path)
                joined = join_video(joinmovies, out_path)
                if not joined:
                    print(error_message+'Error join videos for %s' % datafile)
                    sys.exit(1)
                else:
                    output_files.append(joined.strip())
                    print ('Joined:',joined.strip() )
            else:
                os.rename(join_movies_list[0], out_path)
                output_files.append(out_path.strip())
        # images
        if join_images_list:
            for img_files in join_images_list:
                id, files = list(img_files.items())[0]
                out_image = join(root, 'joined_%s_grp_%s.png' % (id, g))
                if len(img_files)>1:
                    if os.path.exists(out_image):
                        os.remove(out_image)
                    joined = join_images(files, out_image)
                    if not joined:
                        print(error_message+'Error join images for %s' % datafile)
                        sys.exit(1)
                    else:
                        output_files.append(joined.strip())
                        print ('Joined', joined.strip())
                else:
                    joined =  out_image
                    os.rename(files[0], out_image)
                    output_files.append(joined.strip())
    result_files = []
    if not os.path.exists(sdata['review_path']):
        os.makedirs(sdata['review_path'])
    for out_file in output_files:
        new = join(sdata['review_path'], os.path.basename(out_file))
        if os.path.exists(new):
            os.remove(new)
        shutil.copy2(out_file, new)
        result_files.append(new)
        print ('File created:', new)

    sdata['publish_files'] = result_files
    sdata['finished'] = True
    json.dump(sdata, open(datafile, 'w'), indent=4)
    shutil.copy2(datafile, sdata['review_path'])
    finished(sdata['review_path'])
    if sdata.get('postcmd'):
        os.system(sdata.get('postcmd'))
    # os.startfile(datafile)
