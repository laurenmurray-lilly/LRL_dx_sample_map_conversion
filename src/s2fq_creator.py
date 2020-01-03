#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# TODO make paired a global variable
"""
Takes a human-created sample2fastq mapping file in the format sample/tfqr1/fqr2(optional, and gets the dnanexus file ID equivalent GOD BLESS
"""
import os
import argparse
from dxpy.bindings.dxfile_functions import DXFile
from dxpy.bindings.dxproject import DXProject

def extract_from_hpc(s2fq):
    """
    Given a human-created (or intervened) sample to fastq mapping, read the sample ID and associated fastq lane files into a dictionary
    """
    # First check if sample is paired-end
    paired = True
    out = {}
    with open(s2fq, 'r') as s2fq_input_file:
        lines = s2fq_input_file.readlines()
        for line in lines:
            if line.startswith('#'):
                continue
            line = line.strip().split('\t')
            if paired:
                out[line[0]] = [os.path.basename(line[1]), os.path.basename(line[2])]
            else:
                out[line[0]] = [os.path.basename(line[1])]
    return out


def get_file_id_dict(project, folder):
    """
    Get all the file IDs from the upload folder, store them in a dictionary
    the result is a dict with key filename and value file ID
    """
   # new plan, dx describe then get the file ID then return only that
    dx_dict = {}
    project = DXProject(project)
    file_ids = project.list_folder('/'+folder)
    id_dict = file_ids['objects']
    for item in id_dict:
        dx_id = item['id']
        file_object = DXFile(dx_id)
        name = file_object.describe()['name']
        dx_dict[name] = dx_id
    return dx_dict


def get_file_id(file_id_dict, name):
    """
    Given a filename, return the file ID from DNAnexus
    """
    # TODO: first make sure it exists
    return file_id_dict[name]


def construct_dx_s2fq(dx_dict, outfile):
    """
    Given a dictionary of sample to file ID mappings, create the appropriate input text file for the NGS configuration manager
    """
    with open(outfile, 'w+') as out:
        print(dx_dict)
        for sample in dx_dict.keys():
            # TODO only if paired-end
            fastqs = '\t'.join([dx_dict[sample][0], dx_dict[sample][1]])
            out.write('\t'.join([sample, fastqs, '\n']))


def construct_dx_dict(dx_sample_map, string_dict):
    """
    Construct the dictionary of sample to file ID mappings
    """
    out = {}
    for sample in string_dict.keys():
        out[sample] = [get_file_id(dx_sample_map, string_dict[sample][0])]
        # TODO: only if paired-end
        out[sample].append(get_file_id(dx_sample_map, string_dict[sample][1]))
    return out


#TODO: should I pass in a project or folder ID?
def parse_arguments():
    """ parse the CLI """
    parser = argparse.ArgumentParser(description='Extract DNAnexus logs into a tabular format',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s','--s2fq', required = True, help = 'The sample to fastq file generated using string file names')
    parser.add_argument('-f','--folder', required = True, help = 'The folder that the input files are in - the format is just the folder name')
    parser.add_argument('-p', '--projectid', required = True, help = 'DNAnexus project ID. You can find it from Project/Settings page')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    ARGS = parse_arguments()
    S2FQ = ARGS.s2fq
    FOLDER = ARGS.folder
    PROJECT = ARGS.projectid
    STRING_DICT = extract_from_hpc(S2FQ)
    DX_SAMPLE_MAP = get_file_id_dict(PROJECT, FOLDER)
    DXFILE_DICT = construct_dx_dict(DX_SAMPLE_MAP, STRING_DICT)
    # The following creates the output file
    construct_dx_s2fq(DXFILE_DICT, "dx.s2fq.txt")
