'''
Created on Sep 7, 2012

@author: vencax
'''
import os
from django.conf import settings
import datetime

TMPFOLDER = os.path.join(settings.MEDIA_ROOT, '_tmp')
if not os.path.exists(TMPFOLDER):
    os.mkdir(TMPFOLDER)
    
    
def process_chunk(request):
    folder = os.path.join(TMPFOLDER, request.POST['resumableIdentifier'])
    if not os.path.exists(folder):
        os.mkdir(folder)
                
    chunkNumber = request.POST['resumableChunkNumber']
    partFile = os.path.join(folder, chunkNumber)
    if os.path.exists(partFile):
        return
    with open(partFile, 'w') as f:
        f.write(request.FILES['file'].read())
    
    if _is_complete(request, folder):
        newFolder = '%s.complete' % folder
        os.rename(folder, newFolder)
        today = datetime.date.today()
        mergedFName = os.path.join('medialibrary', today.strftime('%Y/%m'),
                                   request.POST['resumableFilename'])
        _mergeChunks(os.path.join(settings.MEDIA_ROOT, mergedFName), newFolder)
        return mergedFName

def _is_complete(request, folder):
    totalSize = int(request.POST['resumableTotalSize'])

    total = 0
    for i in os.listdir(folder):
        total += os.path.getsize(os.path.join(folder, i))
    return total == totalSize

def _mergeChunks(fname, folder):
    if not os.path.exists(os.path.dirname(fname)):
        os.makedirs(os.path.dirname(fname))
    with open(fname, 'w') as merged:
        files = os.listdir(folder)
        files.sort(key=int)
        for i in files:
            with open(os.path.join(folder, i), 'r') as f:
                merged.write(f.read())
                
    for i in os.listdir(folder):
        os.remove(os.path.join(folder, i))
    os.rmdir(folder)