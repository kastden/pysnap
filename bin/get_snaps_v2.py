#!/usr/bin/env python

"""Basic Snapchat client

Usage:
  get_snaps.py -u <username> [-p <password> -q -s -f] <path>

Options:
  -h --help                 Show usage
  -q --quiet                Suppress output
  -s --stories              Download stories instead of snaps
  -f --friends-only         Only download snaps/stories from friends. \
No sponsored content.
  -u --username=<username>  Username
  -p --password=<password>  Password (optional, will prompt if omitted)

"""
from __future__ import print_function

import io
import os
import os.path
import sys
from getpass import getpass
from zipfile import ZipFile

from docopt import docopt

from pysnap import get_file_extension, Snapchat, is_zip


def process_zip(zipobj, unzip_dir, filename_no_ext, file_extension):

    zipped_snap = zipobj
    for file_in_zip in zipped_snap.namelist():
        if file_in_zip.startswith('media'):
            filename = '{0}.{1}'.format(filename_no_ext, file_extension)
        elif file_in_zip.startswith('overlay'):
            filename = '{0}_overlay.png'.format(filename_no_ext)
        else:
            filename = '{0}_{1}'.format(filename_no_ext, file_in_zip)

        abspath_org_filename = os.path.abspath(os.path.join(unzip_dir,
                                                            file_in_zip))
        abspath = os.path.abspath(os.path.join(unzip_dir, filename))

        zipped_snap.extract(file_in_zip, unzip_dir)
        os.rename(abspath_org_filename, abspath)


def process_snap(s, snap, path, quiet=False, is_story=None):

    file_extension = get_file_extension(snap['media_type'])

    if is_story:
        filename_no_ext = snap['id']
    else:
        filename_no_ext = '{0}_{1}'.format(snap['sender'], snap['id'])

    abspath_no_ext = os.path.abspath(os.path.join(path, filename_no_ext))
    abspath = '{0}.{1}'.format(abspath_no_ext, file_extension)

    if os.path.isfile(abspath):
        return

    if is_story:
        data = s.get_story_blob(snap['media_id'],
                                snap['media_key'],
                                snap['media_iv'])
    else:
        data = s.get_blob(snap['id'])

    if data is None:
        return

    if is_zip(data):
        zip = ZipFile(io.BytesIO(data))
        process_zip(zip, path, filename_no_ext, file_extension)
    else:
        with open(abspath, 'wb') as f:
            f.write(data)
    if not quiet:
        print('Saved: {0}'.format(abspath))


def main():
    arguments = docopt(__doc__)
    quiet = arguments['--quiet']
    get_stories = arguments['--stories']
    friends_only = arguments['--friends-only']

    username = arguments['--username']
    if arguments['--password'] is None:
        password = getpass('Password:')
    else:
        password = arguments['--password']
    path = arguments['<path>']

    if not os.path.isdir(path):
        print('No such directory: {0}'.format(path))
        sys.exit(1)

    s = Snapchat()
    if not s.login(username, password).get('logged'):
        print('Invalid username or password')
        sys.exit(1)

    if get_stories:
        get_method = s.get_friend_stories
    else:
        get_method = s.get_snaps

    if get_stories and friends_only:
        friends = [friend['name'] for friend in s.get_friends()]

    for snap in get_method():
        if get_stories and friends_only and snap['sender'] not in friends:
            pass
        else:
            process_snap(s, snap, path, quiet, is_story=get_stories)


if __name__ == '__main__':
    main()
