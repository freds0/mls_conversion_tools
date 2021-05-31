#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# (C) 2021 Frederico Oliveira fred.santos.oliveira@gmail.com
# Released under GNU Public License (GPL)
# Adapted from https://gist.github.com/keithito/771cfc1a1ab69d1957914e377e65b6bd from Keith Ito: kito@kito.us
import argparse
from os.path import exists, join
from pydub import AudioSegment
from pydub.utils import mediainfo
from tqdm import tqdm
from utils.utils import get_filepath_from_link, get_better_quality_link


class Segment:
    '''
    Linked segments Class
    '''
    def __init__(self, begin, end, filesource, filepath):
        self.begin = begin
        self.end = end
        self.next = None
        self.filesource = filesource
        self.filepath = filepath
        self.gap = 0 # gap between segments (current and next)

    def set_next(self, next):
        self.next = next
        self.gap = next.begin - self.end

    def set_filename_and_id(self, filename, id):
        self.filename = filename
        self.id = id

    def merge_from(self, next):
        # merge two segments (current and next)
        self.next = next.next
        self.gap = next.gap
        self.end = next.end

    def duration(self, sample_rate):
        return (self.end - self.start - 1) / sample_rate


def create_segments_list(segments_filepath, sampling_rate = 22050, audio_format = 'wav', output_dir = './'):
    '''
    Creates a linked segment list from a file.
    '''
    extension_file = '.wav' if audio_format == 'wav' else '.flac'
    head = None
    with open(segments_filepath) as f :
        content_data = f.readlines()

        for line in tqdm(content_data):

            filename, link, begin, end = line.strip().split("\t")
            # Get files path
            folder1, folder2, fileid = filename.split('_')
            output_path = join(output_dir, folder1, folder2)
            # Change link 64 to 128
            #link = get_better_quality_link(link)
            # Must be like download_mp3_files function
            mp3_filepath = get_filepath_from_link(link, output_path)
            if not exists(mp3_filepath):
                continue

            output_filepath = join(output_path, filename + extension_file)

            # Verify sample rate
            info = mediainfo(mp3_filepath)
            if int(info['sample_rate']) < int(sampling_rate):
                print('Ignoring {} sr = {}'.format(mp3_filepath, info['sample_rate']))
                continue;

            # Creating segment
            begin = float(begin)*1000
            end = float(end)*1000

            # Build a segment list
            segment = Segment(begin, end, mp3_filepath, output_filepath)
            if head is None:
                head = segment
            else:
                prev.set_next(segment)
            prev = segment

    return head, len(content_data)


def create_audio_files_from_segments_list(head_list, total_files, sampling_rate = 22050, audio_format = 'wav'):
    '''
    Creates audio_tools segments from a linked segment list.
    '''
    curr = head_list
    pbar = tqdm(total=total_files)
    while curr is not None:
        audio_file = curr.filesource
        begin = curr.begin
        end = curr.end
        filepath = curr.filepath
        sound = AudioSegment.from_file(audio_file, frame_rate=sampling_rate, channels=1)
        audio_segment = sound[begin:end]
        #print("Exporting {}".format(filepath))
        try:
            if audio_format == 'wav':
                audio_segment.export(filepath, format = "wav")
            else:
                audio_segment.export(filepath, format = "flac")

        except IOError:
          print("Error: Writing audio_tools file {} problem.".format(filepath))
          return False
        else:
            curr = curr.next
        pbar.update(1)

    pbar.close()
    return True