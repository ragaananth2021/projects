#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# this script is a part of support bundle analyzer script
# this contains all print related functions

from tabulate import tabulate


class PrintFunctions:
    none_msg = ' ' * 15 + 'None'
    print_tilda = '~' * 30

    def display_log_files(self, logfiles):
        """
        Display the name of the logs file
        """

        print("-----> Please find the output of the analysis in the current directory: "
              "The format is 'case-<no>-controller name-bundle date-bundle time.log'")
        for file in logfiles:
            print("")
            print("       * {}".format(file))
            print("")

    def print_output_table(self, logfile, output):
        """
        Function to log switch name, model and uptime
        """

        table = tabulate(output, headers=['Switch Name', 'Model', 'Uptime', 'ASIC type', 'Connected since', 'Role'],
                         tablefmt='grid', colalign=("center", "center", "center", "center", "center", "center",))

        with open(logfile, 'a') as outfile:
            outfile.write(table)
            outfile.write('\n')

    def print_output_audit(self, logfile, output):
        """
        Function to print commands executed by the customer
        """

        for item in output:
            with open(logfile, 'a') as outfile:
                if item is output[0]:
                    outfile.write('<---- Commands for the last month')
                    outfile.write('\n\n')
                    # if the list is empty
                    if not item:
                        outfile.write('~~~~~ No commands executed ~~~~~')
                        outfile.write('\n')
                else:
                    outfile.write('\n')
                    outfile.write('<---- Commands for the current Month')
                    outfile.write('\n\n')
                    # if the list is empty
                    if not item:
                        outfile.write('~~~~~ No commands executed ~~~~~')
                        outfile.write('\n')

            for line in item:
                with open(logfile, 'a') as outfile:
                    outfile.write(' '.join(str(s) for s in line) + '\n')

    @classmethod
    def print_output_dict(cls, logfile, output):
        """
        Function to log list of devices dict and associated values
        """

        with open(logfile, 'a') as outfile:
            for item_key, item_val in output.items():
                outfile.write(cls.print_tilda)
                outfile.write('\n')
                outfile.write("     Switch: {}\n".format(item_key))
                outfile.write(cls.print_tilda)
                outfile.write('\n')

                new_list = []
                for i, j in (list(item_val.items())):
                    new_list.append([i, str(j).strip('[]')])
                table = tabulate(new_list, headers=['Interface', 'Model'],
                                 tablefmt='grid', colalign=("center", "center",))

                outfile.write(table)
                outfile.write('\n')

    @classmethod
    def print_output_dict_simple(cls, logfile, output):
        """
        Function to print a simple dictionary in the following format
        'key'
        'value' <--- type list
        """

        # if the input dict is empty, just log "None"
        if not output:
            with open(logfile, 'a') as outfile:
                outfile.write(cls.none_msg)
                outfile.write('\n')
        else:
            full_list = []

            for k, v in output.items():
                inside_list = [k]
                converted = str(sum(v, [])).strip('[]')
                inside_list.append(converted)
                full_list.append(inside_list)
            table = tabulate(full_list, headers=['Switch name', 'Timeframe of errors'],
                             tablefmt='grid', colalign=("center", "center",))
            with open(logfile, 'a') as outfile:
                outfile.write(table)
                outfile.write('\n')

    @classmethod
    def print_output_dict_custom(cls, logfile, output):
        """
        Function to log list of switches showing errors in ofad-debug
        """

        # if the input dict is empty, just log "None"
        if not output:
            with open(logfile, 'a') as outfile:
                outfile.write(cls.none_msg)
                outfile.write('\n')
        else:
            with open(logfile, 'a') as outfile:
                for item_key, item_value in output.items():
                    outfile.write(cls.print_tilda)
                    outfile.write('\n')
                    outfile.write("     Switch: {}\n".format(item_key))
                    outfile.write(cls.print_tilda)
                    outfile.write('\n')

                    for i, j in item_value.items():
                        # if there are >= 1 occurences of the same error, log it
                        if j >= 1:
                            outfile.write("[{}] - {}".format(str(j).center(5), i))
                            outfile.write('\n')

    def print_header(self, logfile, msg):
        """
        To print headers like "Fabric errors" etc...
        """

        with open(logfile, 'a') as outfile:
            outfile.write('\n')
            outfile.write('<------- {} -------->'.format(msg))
            outfile.write('\n\n\n')

    def print_output(self, logfile, output):

        with open(logfile, 'a') as outfile:
            outfile.write(output)
            outfile.write('\n\n')

