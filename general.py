#!/usr/bin/python3

# developed by Ragavendra Ananth (raga.ananth@bigswitch.com)
# this script is a part of support bundle analyzer script
# this contains all general functions

from datetime import date, timedelta

model_asic_dict = {
    'Z9264': 'Tomahawk 2 ',
    'Z9100-ON': 'Tomahawk ',
    'S6100-ON': 'Tomahawk ',
    'S6010-ON': 'Trident 2+ ',
    'S6000-ON': 'Trident 2 ',
    'S5248F-ON': 'Trident 3 ',
    'S5232F-ON': 'Trident 3 ',
    'S5224F-ON': 'Maverick 2 ',
    'S5212F-ON': 'Maverick 2 ',
    'S5048F-ON': 'Tomahawk+ ',
    'S4148T-ON': 'Maverick ',
    'S4148F-ON': 'Maverick ',
    'S4112F-ON': 'Maverick ',
    'S4112T-ON': 'Maverick ',
    'S4048T-ON': 'Trident 2+ ',
    'S4048-ON': 'Trident 2 ',
    'S3048T-ON': 'Helix4 ',
    'S4810': 'Trident ',
    'AS7816-64X': 'Tomahawk 2 ',
    'AS7726-32X': 'Trident 3 ',
    'AS7412': 'Tomahawk+ ',
    'AS7326': 'Trident 3 ',
    'AS7312-54XS': 'Tomahawk+ ',
    'AS7312-54X': 'Tomahawk ',
    'AS6700': 'Trident 2 ',
    'AS5822-54X': 'Maverick ',
    'AS5712': 'Trident 2',
    'AS5710': 'Trident 2 ',
    'AS5610': 'Trident+ ',
    'AS4600': 'Helix 4 ',
    'AL6960': 'Tomahawk',
    'AS7712': 'Tomahawk',
    'AL6941': 'Trident 2+',
    'AS6812-32X': 'Trident 2+ ',
    'AL6940': 'Trident 2',
    'AS6712': 'Trident 2 ',
    'AL6921-54T': 'Trident 2+',
    'AS5812-54T': 'Trident 2+ ',
    'AL6921-54F': 'Trident 2+',
    'AS5812-54X': 'Trident 2+ '
}


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


def get_last_seven_days(ctrl_path):
    """
    Get the last 7 seven days from the date when support bundle was collected
    """

    bundle_date = ctrl_path.split('/')[-3].split('--')[2].split('-')
    yr = int(bundle_date[0])
    mnt = int(bundle_date[1])
    dy = int(bundle_date[2])
    bd = date(yr, mnt, dy)

    dates = [(bd - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(0, 7)]

    return dates
