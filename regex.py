#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# this script is a part of support bundle analyzer script
# this contains all regex patterns

import re

check_ctrl_pattern = re.compile(r'''
^\d.*                     # ...match each line that starts with a number
(?P<current_ctrl>\*)      # ...followed by a match upto the character '*', name it as as current_ctrl...
.*?(?P<ctrl_state>[a-z]+) # ...followed by a word, which we refer to as state
''', re.VERBOSE)

# this just matches None, literally
none_pattern = re.compile(r'(None)')

# match lines beginning with ~ and ending with None in the next line
# eg: below
# ~ Missing controller inband connection ~
# None.
show_fabric_error_warn_pattern = re.compile(r'^~\s.*\sNone.', re.M)

# match Ci job name followed by anything, then match digit.digit
version_pattern = re.compile(r'Ci job name.*-(?P<version>\d.\d)')

# lookbehind regex
# start from end of the line and match 'No', followed by a word, followed by another word (call it model)
# and lastly match the interface name, call it 'int'
check_hcl_pattern = re.compile(r'(?P<int>[\w:\/]+).*?(?P<model>[\w.+-]+)\s+[\w-]+\s+No(?<=)')

# find the uptime and model of the switch
check_switch_m_u_pattern = re.compile(r'(?sm)up\s(?P<uptime>.*?),\s\s.*Model:\s(?P<model>.*?$)')

# match switch name, connected since and role
check_switch_cntd_since_pattern = re.compile(r'^(?P<swt_name>[\w+-]+)\s(?P<cntd_since>.*?0\s)(?P<role>\w+)$')
