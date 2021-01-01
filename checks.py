#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# this script is a part of support bundle analyzer script
# this contains all functions related to different checks

import logs
import re
import regex
import switch
import controller

ljust_number = 50


def show_fabric_error_warn(active_ctrls, msg, log_file):
    """
    Log fabric errors/warnings if present
    """

    show_fab = 'cli/show-fabric-error'

    with open(active_ctrls + show_fab, 'r') as infile:
        full_file = infile.read()
        # match the lines beginning with ~ and ending with None in the next line
        matches = re.findall(regex.show_fabric_error_warn_pattern, full_file)
        # if there is a match, substitute the match with space
        # this is done so that we see only the interesting output (which are sections with error)
        if matches:
            check_msg = 'Checking for Fabric {}'.format(msg)
            result = '{} found'.format(msg)
            print('{} {}'.format(check_msg.ljust(ljust_number, '.'), result))
            errors = regex.show_fabric_error_warn_pattern.sub('', full_file)
            # remove the blank lines resulting from substituting the matches with ''
            output = ("".join([line for line in errors.strip().splitlines(True) if line.strip()]))
            # write to the log file
            msg = 'FABRIC ERRORS'
            logs.PrintFunctions().print_header(log_file, msg)
            logs.PrintFunctions().print_output(log_file, output)
        else:
            check_msg = 'Checking for Fabric {}'.format(msg)
            result = 'No {} found'.format(msg)
            print('{} {}'.format(check_msg.ljust(ljust_number, '.'), result))


def check_switch_details(active_ctrls, log_file):
    """
    All switch related check go here
    """

    # get the switches in the main directory
    # Eg: from /home/bsn/support/case-11147/bsn-support--BCF-Controller-VM-001--2019-10-02--09-22-52Z--SXI8I

    all_switch_names, switch_name_full_path = switch.get_switch_files(active_ctrls)

    switches_with_i2c_errors, switches_with_smbus_errors, switches_with_non_hcl_optics = \
        switch.check_i2c_errors(switch_name_full_path, active_ctrls)

    switches_with_ofad_errors = switch.check_ofad_logs(switch_name_full_path, active_ctrls)

    switch_model_uptime = switch.check_model_uptime(switch_name_full_path, active_ctrls)

    audit_logs = controller.audit_logs(active_ctrls)

    msg_i2c = "The switches with continuously incrementing i2c errors and the timeframe when maximum " \
              "errors happened are below:"

    logs.PrintFunctions().print_header(log_file, msg_i2c)
    logs.PrintFunctions().print_output_dict_simple(log_file, switches_with_i2c_errors)

    msg_smbus = "The switches with continuously incrementing 'ERR ismt_smbus' and the timeframe " \
                "when maximum errors happened are below:"

    logs.PrintFunctions().print_header(log_file, msg_smbus)
    logs.PrintFunctions().print_output_dict_simple(log_file, switches_with_smbus_errors)

    msg_non_hcl = "The switches with non HCL optics are below:"
    logs.PrintFunctions().print_header(log_file, msg_non_hcl)
    logs.PrintFunctions().print_output_dict(log_file, switches_with_non_hcl_optics)

    msg_ofad = "The switches with errors under ofad-debug logs are below. " \
               "The format is [number of occurences] - error message"
    logs.PrintFunctions().print_header(log_file, msg_ofad)
    logs.PrintFunctions().print_output_dict_custom(log_file, switches_with_ofad_errors)

    msg_model = "The switches and their model number, uptime, ASIC, connection duration and role are below:"
    logs.PrintFunctions().print_header(log_file, msg_model)
    logs.PrintFunctions().print_output_table(log_file, switch_model_uptime)

    msg_audit = "The audit logs for the current and last month are below:"
    logs.PrintFunctions().print_header(log_file, msg_audit)
    logs.PrintFunctions().print_output_audit(log_file, audit_logs)

