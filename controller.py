#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# this script is a part of support bundle analyzer script
# this contains all controller related functions

import os
import re
import regex
from datetime import date, timedelta
import subprocess


def find_ctrl_roles(state, ctrl_dir):
    """
    Based on the state (active or standby), decide which directory is active/standby
    """

    show_ctrl_det = 'cli/show-controller-details'
    all_ctrls = []  # there can be more than one support bundle, hence create a list of all controllers
    for ctrls in ctrl_dir:
        all_ctrls.append(ctrls + show_ctrl_det)

    active_ctrl = []
    standby_ctrl = []
    for ctrls in all_ctrls:
        with open(ctrls, 'r') as infile:
            for line in infile:
                matches = re.search(regex.check_ctrl_pattern, line)
                if matches:
                    # in the current controller directory, if that controller has * and active, then its active
                    # if it has * and standby, then its the standby controller
                    # then strip the last 27 characters (cli/show-controller-details) to reveal the controller directory
                    # eg: /home/bsn/support/00008922/floodlight-support--ICSMCDNETA02--2019-04-26--08-23-06--UTC--3nfm5S
                    # /ICSMCDNETA02-1866daabcc1c/
                    if matches.group('current_ctrl') == '*' and matches.group(
                            'ctrl_state') == 'active' and state == 'active':
                        active_ctrl.append(ctrls[:-27])
                    elif matches.group('current_ctrl') == '*' and matches.group(
                            'ctrl_state') == 'standby' and state == 'standby':
                        standby_ctrl.append(ctrls[:-27])
    if state == 'active':
        return active_ctrl
    else:
        return standby_ctrl


def get_sw_ver(act_ctrl):
    """
    Find the software version of the controller
    """

    show_run = 'cli/show-version-details'
    with open(act_ctrl + show_run, 'r') as infile:
        full_file = infile.read()
        # return the very first match in the file
        matches = regex.version_pattern.search(full_file)
        if matches:
            return matches.group('version')


def get_ctrl_name(ctrl_path, case_number):
    """
    Construct the controller name which will be used as the name of the log file
    Eg: case-11411-bsncontrol01-2019-10-21-17-00-05.log
    """

    folder_name = ctrl_path.split('--')
    # if the input is support bundle path, then the case_number would be set to 'False' under argparse
    # if that's the case, just show the controller name, bundle date and time eg: bsncontrol01-2019-10-21-17-00-05.log
    if not case_number:
        ctrl_name = folder_name[1] + '-' + folder_name[2] + '-' + folder_name[3] + ".log"
    else:
        ctrl_name = 'case-{}'.format(case_number) + '-' + folder_name[1] + '-' + folder_name[2] + '-' + folder_name[3] \
                    + ".log"
    return ctrl_name


def get_var_log_switch_files(ctrl_path):
    """
    Get all the files under ctrl-name/var/log/switch/
    """
    ctrl_path += '/var/log/switch/'

    try:
        all_files = [ctrl_path + file for file in os.listdir(ctrl_path) if file.endswith('.log')]
    except OSError:
        return None
    return all_files


def get_bundle_details(act_ctrl):
    """
    Find when the bundle was collected
    """

    bundle_date = act_ctrl.split('--')[2]
    bundle_time = act_ctrl.split('--')[3]

    return bundle_date, bundle_time


def get_month_list(ctrl_path):
    """
    Get the month from when the support bundle was collected and find the previous month
    """

    bundle_date = ctrl_path.split('--')[2].split('-')
    yr = int(bundle_date[0])
    mnt = int(bundle_date[1])
    dy = int(bundle_date[2])
    bd = date(yr, mnt, dy)

    # last day of last month
    prev_month = (bd.replace(day=1) - timedelta(days=1))
    curr_month = bd.replace(day=1)  # current month

    # get the last/current month, year
    last_month = prev_month.strftime('%Y-%m')
    this_month = curr_month.strftime('%Y-%m')

    month_list = [last_month, this_month]
    return month_list


def audit_logs(act_ctrl):
    """
    Find the audit logs for the current and past month and add them to a list, grouped by the month
    The first element would be last month and the second element would be the current month
    """

    # get the sw version
    ctrl_sw_version = get_sw_ver(act_ctrl)

    # for bundles on BCF 5.x, the audit log file is located under act_ctrl_dir/files/var/log/floodlight/
    if ctrl_sw_version.startswith('5'):
        act_ctrl = act_ctrl + 'files/'

    months = get_month_list(act_ctrl)
    output_list = []

    for month in months:
        month_list = []
        # the below pattern would look for commands executed by the user
        # the pattern would result in 2019-11-22T11:26:28.479+00:00 executed_command
        check_audit_log_pattern = re.compile(r'(?P<mnth>{}.*?00\s).*?id=.*?args=\"(?P<cmd>.*)\"'.format(month))
        with open(act_ctrl + 'var/log/floodlight/audit.log') as infile:
            for line in infile:
                matches = re.search(check_audit_log_pattern, line)
                if matches:
                    # create a lambda function to check if the user had entered space or pressed enter
                    # in those cases, the output will be an empty string, which we do not want to show
                    not_empty = lambda cmd: bool(cmd and cmd.strip())
                    # if True, add those commands to the corresponding month's list
                    if not_empty(matches.group('cmd')):
                        executed_cmd = (matches.group('mnth'), matches.group('cmd'))
                        month_list.append(executed_cmd)
        output_list.append(month_list)

    return output_list
