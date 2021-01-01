#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# the script automates the support bundle analysis and executes a checklist
#
# The script does the following:
#
# Handle multiple support bundles in the directory
# Input can be either case number or path to a support bundle directory
# Check for fabric errors
# Check for continuously incrementing i2c and ismt_smbus errors (since we need to focus mainly on those errors) for the last 7 days, print when it happened
# Check for non-hcl optics used in the switches and for those interfaces, print the interface name and optics model
# Check for critical, error, exception messages in switch ofad-debug logs for the last 7 days and print the no. of times it happened along with the message
# Print the switch name, model, role, connected duration and uptime in a tabular format
# Present the output in a single log file

import os
import sys
import argparse
import logs
import controller
import checks
import time
from pathlib import Path


class CheckList:
    """
    Execute the below checklist.
    """
    starttime = time.time()
    logfiles = []

    def __init__(self, active, case_num):
        self.active = active
        self.case_num = case_num

        for active_ctrls in self.active:
            # create a file name based on the controller name, date and time
            ctrl_file_name = controller.get_ctrl_name(active_ctrls, case_num)
            self.logfiles.append(ctrl_file_name)
            # get bundle date and time it was collected
            bundle_date, bundle_time = controller.get_bundle_details(active_ctrls)
            print('')
            msg = "Analyzing the bundle collected on {} at {}".format(bundle_date, bundle_time)
            print(msg)
            print('~' * len(msg))
            print('')

            # erase the contents on the file if it was run previously
            with open(ctrl_file_name, 'w'): pass
            # execute the below check to find fabric errors
            checks.show_fabric_error_warn(active_ctrls, 'errors', ctrl_file_name)

            checks.check_switch_details(active_ctrls, ctrl_file_name)

            print(".....Done.....")
            print("")


class LogFiles(CheckList):
    """
    Inherit the log files and starttime from the parent class CheckList
    """

    @classmethod
    def show_log_files(cls):
        logs.PrintFunctions().display_log_files(cls.logfiles)

        print('The analysis took {} seconds'.format(time.time() - cls.starttime))
        print('')


# class to validate case directory and controller directories
class DirValidation(object):

    def validate_case_num(self, case_num):
        """
        Check for the case directory and return the path
        eg: /home/bsn/support/case-11146/
        """

        # there can be multiple directories with the case number
        # eg: 00011705 or case00011705
        path = []
        print("Checking if support bundle exists...")
        srcdir = '/home/bsn/support'
        for dirs in os.listdir(srcdir):
            if case_num in dirs:
                # add the directories to the list
                path.append(os.path.join(srcdir, dirs, ''))

        return path

    def validate_bundle_dir(self, bundle_dir):
        """
        Check for the support bundle directory and return the path as a list
        eg: ['/home/bsn/support/daneco/']
        The reason for returning the path as a list is due to the check "for each_dir in valid_path:"
        """

        bundle_loc = []
        # check if user provided the path with / at the end
        # if not, add / to the end
        if not bundle_dir.endswith('/'):
            bundle_dir += os.sep

        print("Checking if the path exists...")
        if os.path.isdir(bundle_dir):
            # check if this is a support bundle directory
            for dirs in os.listdir(bundle_dir):
                # check if it's a directory
                if os.path.isdir(os.path.join(bundle_dir, dirs)):
                    # consider only the directories that starts with floodlight or bsn
                    if dirs.startswith(('floodlight-support--', 'bsn-support--')):
                        # all checked out OK, return the main dir
                        bundle_loc.append(bundle_dir)
                        return bundle_loc
                    else:
                        print("The path exists but there are no support bundles")
                        sys.exit(-1)

    def find_controller_directories(self, path):
        """
        Check if there are more than one support bundles. Return the controller directories for all the support bundles
        in the case directory
        """

        # main_dir is the parent folder eg: floodlight-support--IEIL-CNTRL1-10-10-200-48--2019-11-26--17-57-21--IST
        main_dirs = []
        for dirs in os.listdir(path):
            # consider only the directories that starts with floodlight or bsn
            if dirs.startswith(('floodlight-support--', 'bsn-support--')):
                if os.path.isdir(os.path.join(path, dirs)):
                    main_dirs.append(dirs)
        all_dirs = []
        for dirs in main_dirs:
            new_path = path + dirs + '/'
            controllers = []
            for ctrl_dirs in os.listdir(new_path):
                if os.path.isdir(os.path.join(new_path, ctrl_dirs)):
                    controllers.append(ctrl_dirs)
            for _main_dir in controllers:
                _ctrl_dir = new_path + _main_dir
                all_dirs.append(_ctrl_dir + "/")

        # check if it's actually a controller directory since the customer might have created some additional dir
        controller_dir = []
        cli_dir = 'cli'
        for dir in all_dirs:
            # check if the controller directory has a cli directory and add only those directories to the list
            dir_with_cli = dir + cli_dir
            if os.path.exists(dir_with_cli):
                controller_dir.append(dir)
        return controller_dir, len(main_dirs)


class UserinputPathcheck:

    def __init__(self, input_path):
        self.input_path = input_path
        self.corrected_path = ''

    def correct_the_path(self):

        home_folder = Path(self.input_path).home()
        home_folder_parent = Path(self.input_path).home().parent
        tild_with_slash = '~/'
        tild = '~'

        # if user provided a path like '~/support/eumesat-ps'
        if self.input_path.startswith(tild_with_slash):
            self.corrected_path = self.input_path.replace(tild_with_slash, str(home_folder))
        # if user provided a path like '~bsn/support/eumesat-ps'
        elif self.input_path.startswith(tild):
            self.corrected_path = self.input_path.replace(tild, str(home_folder_parent) + os.sep)
        else:
            self.corrected_path = self.input_path

        return self.corrected_path


if __name__ == '__main__':

    # Get the case number from user and check if the directory with the case number exists.
    # After the check passes, proceed to find the controller directories in the case directory

    parser = argparse.ArgumentParser(description='support bundle analyzer script')
    # the user could provide a case number or path to a support bundle
    inp = parser.add_mutually_exclusive_group(required=True)

    inp.add_argument("-c", "--case-num", action='store', default=False, help="Enter the case number")
    inp.add_argument("-p", "--path", action='store', default=False,
                     help="Enter the path to the support bundle")

    user_input = parser.parse_args()

    case_number = user_input.case_num
    bundle_path = user_input.path

    valid_path = None
    if case_number:
        try:
            # check if the directory with the case number exist
            valid_path = DirValidation().validate_case_num(case_number)
            if not valid_path:
                raise OSError
        except OSError:
            print(
                "The directory with case number {} is not found. The customer hasn't uploaded the support bundle.".format(
                    case_number))
            sys.exit(-1)
    elif bundle_path:
        # sanitize the input path
        bundle_dir = UserinputPathcheck(bundle_path).correct_the_path()
        try:
            # check if the provided directory exists
            valid_path = DirValidation().validate_bundle_dir(bundle_dir)
            if not valid_path:
                raise OSError
        except OSError:
            print("The directory {} is not found. Please double check the path".format(bundle_dir))
            sys.exit(-1)

    # inform the user that multiple support bundle directories are found for the same case number
    if len(valid_path) == 1:
        print('Support bundle found at the following location')
        print("-----> {}".format(valid_path[0]))
    else:
        print('Multiple support bundle directories found for the same case number at the following locations')
        for each_path in valid_path:
            print("-----> {}".format(each_path))

    # find the controller directories in the found paths
    for each_dir in valid_path:
        ctrl_dirs, num_of_bundles = DirValidation().find_controller_directories(each_dir)
        if ctrl_dirs:
            print('')
            print('Now analyzing the location {} ...'.format(each_dir))
            print('')
            if num_of_bundles > 1:
                print("It looks like there are more than one support bundles at {}\n".format(each_dir))
                print("All bundles will be analyzed.")
        else:
            print("Support bundle(s) found at {}".format(each_dir))
            print("/cli directory is not available under the controller directory... bundle could be corrupted\n"
                  "Please try untarring the bundle again or ask the customer to re-upload the support bundle...\n"
                  "### ERROR ### The script cannot proceed\n")
            print("Exiting...")
            sys.exit(-1)

        # find the active and standby controller directory and setup logfile for active controller(s)
        active = controller.find_ctrl_roles('active', ctrl_dirs)
        print("Please find below the active controller directory for all the support bundles")
        if active:
            for ctrls in active:
                print("The Active controller is at {}".format(ctrls))
        else:
            print("No Active controller directory found")

        print('')

        # execute the checks
        CheckList(active, case_number)

    # finally display all the logfiles
    LogFiles.show_log_files()

    sys.exit(0)
