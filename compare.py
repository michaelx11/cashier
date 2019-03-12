# Loads in two cash files and walks them, printing differences
import json
import sys

verbose = False

def print_verbose(s):
    if verbose:
        print(s)

def compare_recur(co1, co2, is_dir=False):
    # Is there even a difference?
    if co1['hash'] == co2['hash'] and co1['namehash'] == co2['namehash']:
        # No need to check!
        return
    print('{}{}'.format(co1['dirname'], '/' if is_dir else ''))
    print_verbose('= {} differs =\n1:{}-{}\n2:{}-{}'.format(
        co1['dirname'],
        co1['hash'],
        co1['namehash'],
        co2['hash'],
        co2['namehash']))
    # Same procedure for subfiles and subdirs
    for keyname in ['subfiles', 'subdirs']:
        # = Go through subfiles =
        # build a dict on co1 subfiles keyed by dirname
        co1_sf_dict = {}
        for sf1 in co1.get(keyname, []):
            co1_sf_dict[sf1['dirname']] = sf1
        co2_sf_dict = {}
        for sf2 in co2.get(keyname, []):
            co2_sf_dict[sf2['dirname']] = sf2
        for common_dirname in co1_sf_dict.keys() & co2_sf_dict.keys():
            compare_recur(co1_sf_dict[common_dirname], co2_sf_dict[common_dirname], is_dir=keyname == 'subdirs')
        for co1_dir in co1_sf_dict.keys() - co2_sf_dict.keys():
            print('>>>! {}{}'.format(co1_dir, '/' if keyname == 'subdirs' else ''))
            print_verbose('= {} differs ='.format(co1_dir))
            print_verbose('{}: {} in 1 but not 2'.format(keyname, co1_dir))
        for co2_dir in co2_sf_dict.keys() - co1_sf_dict.keys():
            print('!<<< {}{}'.format(co2_dir, '/' if keyname == 'subdirs' else ''))
            print_verbose('= {} differs ='.format(co2_dir))
            print_verbose('{}: {} in 2 but not 1'.format(keyname, co2_dir))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python compare.py [.cash_file1] [.cash_file2]')
        sys.exit(1)

    with open(sys.argv[1], 'r') as cash1:
        with open(sys.argv[2], 'r') as cash2:
            compare_recur(json.load(cash1), json.load(cash2), is_dir=True)
