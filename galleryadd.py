#!/usr/bin/env python
#
# A Python implementation compatible with the command-line API for
# galleryadd.pl (http://codex.galleryproject.org/Downloads:Galleryadd.pl_NG)
# because it seems to no longer be available
#
# The Python implementation requires the GalleryRemote python package
# (http://pietrobattiston.it/galleryremote).
#
# Copyright (c) 2015 Michael Ihde
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from optparse import OptionParser
import os
import sys

try:
    from galleryremote.gallery import Gallery, GalleryException
except ImportError:
    print >> sys.stderr, \
        "Could not find galleryremote.  " \
        "Have you installed http://pietrobattiston.it/galleryremote"
    sys.exit(-1)

parser = OptionParser()

parser.add_option("-g", "--gallery")
parser.add_option("-G", "--gallery-version",
        default=1)

parser.add_option("-u", "--user")
parser.add_option("-p", "--password")


parser.add_option("-a", "--album")
parser.add_option("-c", "--create")
parser.add_option("-d", "--description")
parser.add_option("-t", "--title")
parser.add_option("-P", "--parent",
        default=0)

parser.add_option("-C", "--caption")
parser.add_option("-z", "--zap-caption",
        action="store_true",
        default=False)

parser.add_option("-r", "--recursive",
        action="store_true",
        default=False)
parser.add_option("-l", "--list",
        action="store_true",
        default=False)
parser.add_option("-n", "--no-verify",
        dest="verify",
        action="store_false",
        default=True)
parser.add_option("-S", "--skip-existing",
        action="store_true",
        default=False)

parser.add_option("-q", "--quiet",
        action="store_true",
        default=False)

parser.add_option("-v", "--verbose",
        action="store_true",
        default=False)

opts, args = parser.parse_args()

gallery = Gallery(opts.gallery, opts.gallery_version)

if opts.user and opts.password:
    gallery.login(opts.user, opts.password)

if opts.list or opts.verify:
    albums = gallery.fetch_albums()

if opts.create:
    if opts.verify and opts.parent:
        album = albums.get(opts.album, None)
        if not album:
            parser.error("parent album {0} doesn't exist".format(
                opts.album))
        if album.get("perms.create_sub") != "true":
            parser.error("user {0} doesn't have permission to create to album {1} in {2}".format(
                opts.user, opts.album, opts.parent))

    gallery.new_album(
            parent=opts.parent,
            name=opts.create,
            title=opts.title,
            description=opts.description)
    opts.album = opts.create
    albums = gallery.fetch_albums()

if opts.list:
    for album in sorted(albums.values(), key=lambda x: x.get('name')):
        print "{name:24} {title}".format(**album)
        print album

if opts.verify:
    album = albums.get(opts.album, None)
    if not album:
        parser.error("album {0} doesn't exist".format(
            opts.album))
    if album.get("perms.add") != "true" or album.get("perms.write") != "true":
        parser.error("user {0} doesn't have permission to write to album {1}".format(
            opts.user, opts.album))

if opts.album and args:
    # Get existing items, if necessary
    if opts.skip_existing:
        existing = set([img["name"] for img in gallery.fetch_album_images(opts.album)])
    else:
        existing = set()

    # Add items
    for item in args:
        if os.path.isfile(item):
            # Deal with captions and descriptions
            if opts.zap_caption == True:
                caption = ""
            elif opts.caption == None:
                caption = os.path.basename(item)
            if opts.description == None:
                description = ""
            # Skip files that have already been uploaded
            if os.path.basename(item) in existing:
                if not opts.quiet:
                    print "skipping {0}".format(item)
                continue
            # Upload item
            if not opts.quiet:
                print "adding {0} to {1} ...".format(item, opts.album),
            try:
                gallery.add_item(album['name'],
                        item,
                        caption=caption,
                        description=description)
            except GalleryException, e:
                print "failed: {0}".format(e)
            else:
                if not opts.quiet:
                    print "done"
        elif os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                for filename in sorted(files):
                    # Deal with captions and descriptions
                    if opts.zap_caption == True:
                        caption = ""
                    elif opts.caption == None:
                        caption = os.path.basename(filename)
                    if opts.description == None:
                        description = ""
                    # Skip files that have already been uploaded
                    if os.path.basename(filename) in existing:
                        if not opts.quiet:
                            print "skipping {0}".format(filename)
                        continue
                    # Upload item
                    if not opts.quiet:
                        print "adding {0} to {1} ...".format(filename, opts.album),
                    try:
                        gallery.add_item(album['name'],
                                os.path.join(root, filename),
                                caption=caption,
                                description=description)
                    except GalleryException, e:
                        print "failed: {0}".format(e)
                    else:
                        if not opts.quiet:
                            print "done"
                if not opts.recursive:
                    del dirs[:]
