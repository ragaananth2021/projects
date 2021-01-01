#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# this script is a part of support bundle analyzer script
# this contains all switch related functions

import os
import subprocess
from collections import OrderedDict
from tqdm import tqdm
import re
import controller
import general
import regex


def get_switch_files(act_ctrl):
    """
      Find all the switch files under the main dir and return a list with only the name of the switch
      """

    new_whole_str = act_ctrl.split("/")  # split using the '/' separator
    main_dir = '/'.join(new_whole_str[:-2])  # join upto the main dir
    swt_name_pattern = '-fe80::'  # make sure the function returns only switch files and not customer created files
    switch_files = []
    for files in os.listdir(main_dir):
        if os.path.isfile(os.path.join(main_dir, files)):
            if swt_name_pattern in files:
                switch_files.append(files)
    all_switch_names = [i.split('-fe80')[0] for i in switch_files]  # return a list with only the name of the switch
    # return a list with the whole name of the switches with full path
    # eg: /home/bsn/.../LIMSPINER3-1-fe80::e6f0:4ff:fe0a:6c2d%10
    switch_name_full_path = [main_dir + os.sep + i for i in switch_files]

    return all_switch_names, switch_name_full_path


def find_continuous_errors(switch, output_full, output):
    """
    search for continuous i2c/smbus errors
    """
    all_ts = dict()
    switches_with_errors_all_max = dict()
    timestamp = []
    for timestp in output.decode().split('\n'):
        timestamp.append(timestp)

    # find all occurences of the errors
    # create a dict with key as timestamp and num of occurences as value
    all_occurences = OrderedDict()
    for each_timestamp in timestamp:
        count = 0
        # check if the same timestamp occurs in the full output
        for line in output_full.decode().split('\n'):
            if each_timestamp in line:
                count += 1
                all_occurences[each_timestamp] = count

    # if errors occur more than 5 times continuously, log that timestamp and value
    for ts, cnt in all_occurences.items():
        if all_occurences[ts] > 5:
            all_ts.setdefault(ts, []).append(all_occurences[ts])

    # find the max value only for dicts with values (ignore empty dicts)
    if all_ts:
        max_key = max(all_ts, key=lambda k: max(all_ts.get(k)))
        switches_with_errors_all_max.setdefault(switch, []).append(max_key)

    return switches_with_errors_all_max


def check_i2c_errors(switch_files, act_ctrl):
    """
      Check for the following:
      continuosly increasing i2c errors on the switches for the last 7 days
      continuosly increasing smbus errors on the switches for the last 7 days
      non-hcl optics
      """

    # get the sw version
    ctrl_sw_version = controller.get_sw_ver(act_ctrl)

    # for bundles on BCF 5.x, the switch log files are located under act_ctrl_dir/files/var/log/switch/
    if ctrl_sw_version.startswith('5'):
        act_ctrl = act_ctrl + 'files'

    # get the files under /var/log/switch/
    var_log_switch_files = controller.get_var_log_switch_files(act_ctrl)

    # get the last 7 days
    dates = general.get_last_seven_days(act_ctrl)

    switches_with_non_hcl_optics = {}
    switches_with_max_i2c_timeframe = {}
    switches_with_max_smbus_timeframe = {}
    smbus_switch_names = {}

    print("Checking for continuous switch i2c errors for the last 7 days...")

    with tqdm(total=len(dates)) as pbar:

        for day in dates:
            for switch in switch_files:
                # search for continuous i2c errors in all the switch files
                cmd_full = "grep -a 'error.*i2c-' {} | awk '{{print substr($0,1,16)}}' | grep {} | sort".format(switch,
                                                                                                                day)
                output_full = (subprocess.Popen(cmd_full, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()

                cmd = "grep -a 'error.*i2c-' {} | awk '{{print substr($0,1,16)}}' | grep {} | sort | uniq".format(
                    switch, day)
                output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()

                max_timeframe_i2c = find_continuous_errors(switch, output_full, output)
                switches_with_max_i2c_timeframe.setdefault(switch, []).append(max_timeframe_i2c)

            pbar.update(1)

    i2c_switch_timeframe = {}
    for each_switch in switch_files:
        switch = switches_with_max_i2c_timeframe[each_switch]
        for i in switch:
            for a, b in i.items():
                i2c_switch_timeframe.setdefault(a, []).append(b)

    print("Checking for continuous switch smbus errors for the last 7 days...")

    # sometimes, there are no switch logs under /var/log/switch
    # hence, do the below only if there are switch log files
    if var_log_switch_files:
        with tqdm(total=len(dates)) as pbar:
            for day in dates:
                # search 'ERR ismt_smbus' in all the files under /var/log/switch folder of the controller
                for file in var_log_switch_files:
                    cmd_full = "zgrep 'ERR ismt_smbus' {} | awk '{{print substr($0,1,16)}}' | grep {}".format(file, day)
                    output_full = (subprocess.Popen(cmd_full, stdout=subprocess.PIPE, shell=True)).communicate()[
                        0].strip()

                    cmd = "zgrep 'ERR ismt_smbus' {} | awk '{{print substr($0,1,16)}}' | grep {} | sort | uniq".format(
                        file,
                        day)
                    output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()

                    max_timeframe_smbus = find_continuous_errors(file, output_full, output)
                    switches_with_max_smbus_timeframe.setdefault(file, []).append(max_timeframe_smbus)

                pbar.update(1)

        smbus_switch_timeframe = {}
        for each_switch in var_log_switch_files:
            switch = switches_with_max_smbus_timeframe[each_switch]
            for i in switch:
                for a, b in i.items():
                    smbus_switch_timeframe.setdefault(a, []).append(b)

        # construct the switch name from the path
        for switch_name, time_frame in smbus_switch_timeframe.items():
            sw = switch_name.split('/')[-1].split('.')[0]
            smbus_switch_names[sw] = smbus_switch_timeframe[switch_name]
    else:
        # if there are no files, return a empty dict
        print('...No switch logs found under /var/log/switch/...')
        smbus_switch_names = {}

    print("Checking for non HCL optics for the switches...")
    # find non-hcl optics

    with tqdm(total=len(switch_files)) as pbar:
        for file in switch_files:

            cmd = "grep -a 'inventory hcl' -A 100 {}".format(file)
            output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0]

            # create a int_model dict to store the interface and model number
            int_model = OrderedDict()

            for line in output.decode().split('\n'):
                matches = re.search(regex.check_hcl_pattern, line)
                if matches:
                    # add the 'interface' and 'model' to the dict
                    int_model.setdefault(matches.group('int'), []).append(matches.group('model'))
                    # construct the switch name from the path
                    switch_name = file.split('/')[-1].split('-fe80')[0]
                    # with switch_name as the key, assign the dict to the key
                    switches_with_non_hcl_optics[switch_name] = int_model
            pbar.update(1)

    # construct the switch name from the path
    i2c_switch_names = {}
    for switch_name, time_frame in i2c_switch_timeframe.items():
        sw = switch_name.split('/')[-1].split('-fe80')[0]
        i2c_switch_names[sw] = i2c_switch_timeframe[switch_name]

    return i2c_switch_names, smbus_switch_names, switches_with_non_hcl_optics


def check_ofad_logs(switch_files, act_ctrl):
    switches_ofad_errors = {}
    dates = general.get_last_seven_days(act_ctrl)
    date_pattern = 'T|'.join(dates)

    print("Checking for ofad errors on the switches for the last 7 days...")

    with tqdm(total=len(switch_files)) as pbar:
        for swt in switch_files:
            error_dict = {}
            grep_pattern = "| grep -E 'exception \[|error \[|critical \[' | grep -v icmpa | grep -E '{}' ".format(
                date_pattern)
            awk_pattern = "| awk -F\"[ ]\" '{ $1=\"\"; print $0 }' | sort | uniq"
            # sample cmd syntax. Ignore icmpa errors
            # cat <path to switch file>| grep -E 'exception \[|error \[|critical \[' | grep -v icmpa | grep -E '<dates>' | awk -F"[ ]" '{ $1=""; print $0 }' | sort | uniq
            cmd = "cat " + swt + grep_pattern + awk_pattern
            output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()

            if output:
                for line in output.decode().split('\n'):
                    cmd = "grep -F \"{}\" ".format(line) + swt + " | wc -l"
                    output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()
                    # append the number of occurences and the error message
                    error_dict[line] = int(output)
                    switch_name = swt.split('/')[-1].split('-fe80')[0]
                    # with switch_name as the key, assign the dict to the key
                    switches_ofad_errors[switch_name] = error_dict

            pbar.update(1)
    return switches_ofad_errors


def check_model_uptime(switch_files, act_ctrl):
    """
    Find the switch model and it's uptime
    """

    show_switch = 'cli/show-switch-all-details'
    all_swt_info = []
    for swt in switch_files:
        current_swt = []
        cmd = "cat " + swt + "| grep -aE -A 2 '^Model|uptime'"
        output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()
        # find out the uptime and model
        matches = re.findall(regex.check_switch_m_u_pattern, output.decode())
        switch_name = swt.split('/')[-1].split('-fe80')[0]
        # append the switch name, model and uptime to a list
        current_swt.append(switch_name)
        model = matches[0][1]
        current_swt.append(model)
        uptime = matches[0][0]
        current_swt.append(uptime)
        # find the switch ASIC
        if model in general.model_asic_dict:
            # append the ASIC type
            current_swt.append(general.model_asic_dict[model])
        else:
            # if not found, append blank
            current_swt.append(' ')
        show_switch_details = act_ctrl + show_switch
        # get the switch name, connected since and role
        cmd = "cat " + show_switch_details + "| awk '{print $2, $6, $7, $14}'"
        output = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)).communicate()[0].strip()
        for line in output.decode().split('\n'):
            matches = re.search(regex.check_switch_cntd_since_pattern, line)
            if matches:
                if matches.group('swt_name') == switch_name:
                    current_swt.append(matches.group('cntd_since'))
                    current_swt.append(matches.group('role'))
        # append the current list to the master list
        all_swt_info.append(current_swt)

    return all_swt_info
