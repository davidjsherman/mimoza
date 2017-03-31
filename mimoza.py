# !/usr/bin/env python
# encoding: utf-8

from sbml_vis.mimoza_pipeline import process_sbml

__author__ = 'anna'

if __name__ == "__main__":

    # parameter parsing #
    import argparse

    parser = argparse.ArgumentParser(description="Generalizes and visualizes an SBML model.")
    parser.add_argument('--model', required=True, type=str, help="input model in SBML format")
    parser.add_argument('--generalize', action='store_true', help='whether to generalize the model')
    parser.add_argument('--output_dir', default=None, type=str,
                        help="The name of the directory that will store the visualisation "
                             "(if left blank md5 code of the model file will be used). "
                             "This directory will be created in the same place where the input model file is located.")
    parser.add_argument('--verbose', action="store_true", help="print logging information")
    parser.add_argument('--log', default=None, type=str, help="file to redirect logging information to")
    params = parser.parse_args()

    process_sbml(params.model, params.verbose, ub_ch_ids=None, web_page_prefix=params.output_dir,
                 generalize=params.generalize, log_file=params.log)
