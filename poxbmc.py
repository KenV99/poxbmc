#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 KenV99
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import os
import fnmatch
import re
import operator
import traceback

__cwd__ = os.getcwd().encode('utf-8')
podict = None

###############  OPTIONS  ###########################
root_directory_to_scan = __cwd__  # put whichever directory you want here
exclude_files = ['poxbmc.py']
exclude_directories = ['localized']  # use 'subdir\\subberdir' to designate deeper
output_directory = os.path.join(__cwd__, 'localized')
current_working_English_strings_po = os.path.join(__cwd__, r'resources\language\English\strings.po')  # set to None
#  is there isn't one
option_add_commented_string_when_localizing = True

# tag lines to look for quoted strings with '# @@' (only the part within the quotes)
# triple quoted multiline strings are NOT supported
# please ensure double quotes within strings are properly escaped with \"
# WARNING: all files in output_directory will be overwritted!

#####################################################


class PoDict():

    def __init__(self):
        self.dict_msgctxt = dict()
        self.dict_msgid = dict()

    def get_new_key(self):
        mmax = max(self.dict_msgctxt.iteritems(), key=operator.itemgetter(0))[0]
        try:
            int_key = int(mmax)
        except ValueError:
            int_key = -1
        return int_key + 1

    def addentry(self, str_msgctxt, str_msgid):
        self.dict_msgctxt[str_msgctxt] = str_msgid
        self.dict_msgid[str_msgid] = str_msgctxt

    def has_msgctxt(self, str_msgctxt):
        if str_msgctxt in self.dict_msgctxt:
            return [True, self.dict_msgctxt[str_msgctxt]]
        else:
            return [False, None]

    def has_msgid(self, str_msgid):
        if str_msgid in self.dict_msgid:
            return [True, self.dict_msgid[str_msgid]]
        else:
            return [False, str(self.get_new_key())]

    def read_from_file(self, url):
        if url is None:
            return
        if os.path.exists(url):
            with open(url, 'r') as f:
                poin = f.readlines()
            i = 0
            while i < len(poin):
                line = poin[i]
                if line[0:7] == 'msgctxt':
                    t = re.findall(r'".+"', line)
                    str_msgctxt = t[0][2:7]
                    i += 1
                    line2 = poin[i]
                    str_msgid = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line2)[0]
                    self.dict_msgctxt[str_msgctxt] = str_msgid
                    self.dict_msgid[str_msgid] = str_msgctxt
                i += 1

    def write_to_file(self, url):
        fo = open(url, 'w')
        self.write_po_header(fo)
        for str_msgctxt in sorted(self.dict_msgctxt):
            self.write_to_po(fo, str_msgctxt, self.format_string_forpo(self.dict_msgctxt[str_msgctxt]))
        fo.close()

    def format_string_forpo(self, mstr):
        out = ''
        for (i, x) in enumerate(mstr):
            if i == 1 and x == r'"':
                out += "\\" + x
            elif x == r'"' and mstr[i-1] != "\\":
                out += "\\" + x
            else:
                out += x
        return out

    def write_po_header(self, fo):
        fo.write('# XBMC Media Center language file\n')
        fo.write('# Addon Name: ???\n')
        fo.write('# Addon id: ???\n')
        fo.write('# Addon Provider: ???\n')
        fo.write('msgid ""\n')
        fo.write('msgstr ""\n')
        fo.write('"Project-Id-Version: XBMC Addons\\n"\n')
        fo.write('"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n')
        fo.write('"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n')
        fo.write('"MIME-Version: 1.0\\n"\n')
        fo.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
        fo.write('"Content-Transfer-Encoding: 8bit\\n"\n')
        fo.write('"Language: en\\n"')
        fo.write('"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n\n\n')

    def write_to_po(self, fileobject, int_num, str_msg):
        w = r'"#' + str(int_num) + r'"'
        fileobject.write('msgctxt ' + w + '\n')
        fileobject.write('msgid ' + r'"' + str_msg + r'"' + '\n')
        fileobject.write('msgstr ' + r'""' + '\n')
        fileobject.write('\n')


def examinefile(pyin, pyout):
    global podict

    def match_fix(singmatch, dblmatch):
        matches = []
        dblchk = []
        if len(singmatch) > 0 and len(dblmatch) == 0:
            return singmatch
        elif len(dblmatch) > 0 and len(singmatch) == 0:
            return dblmatch
        elif len(dblmatch) == 0 and len(singmatch) == 0:
            return []
        else:
            for match1 in singmatch:
                for match2 in dblmatch:
                    if match1 == match2:
                        dblchk.append(match1)
                    elif match1 in match2:
                        match_append_chk(match2, matches)
                    elif match2 in match1:
                        match_append_chk(match1, matches)
                    else:
                        match_append_chk(match1, matches)
                        match_append_chk(match2, matches)
            matches2 = matches
            for match1 in dblchk:
                for match2 in matches:
                    if match1 in match2:
                        if len(match1) > len(match2):
                            matches2.append(match1)
            return matches2

    def match_append_chk(match, matches):
        if not (match in matches):
            matches.append(match)

    try:
        match_btwn_singq = re.compile(r"'([^'\\]*(?:\\.[^'\\]*)*)'")
        match_btwn_dblq = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
        match_tag_examine = re.compile(r'# @@')
        match_tag_comment = re.compile(r'\# @.+')
        match_localized_txt = re.compile('__language__\(.+?\)')
        for line in pyin:
            if line.strip()[0:1] == "#":
                pyout.write(line)
                continue
            if match_tag_examine.search(line) is not None:
                singmatch = match_btwn_singq.findall(line)
                dblmatch = match_btwn_dblq.findall(line)
                matches = match_fix(singmatch, dblmatch)
                if len(matches) > 0:
                    newline = line
                    term = '# @'
                    x = ''
                    for match in matches:
                        res = podict.has_msgid(match)
                        if res[0]:
                            outnum = res[1]
                        else:
                            outnum = res[1]
                            podict.addentry(outnum, match)
                        repl = '__language__(%s)' % outnum
                        if match in singmatch:
                            y = match_btwn_singq.sub(repl, newline, 1)
                        else:
                            y = match_btwn_dblq.sub(repl, newline, 1)
                        if option_add_commented_string_when_localizing:
                            term = term + '[%s] ' % match
                            newline = y
                            x = y.replace('# @@', term, 1)
                        else:
                            newline = y
                            x = y
                    pyout.write(x)
            else:
                if option_add_commented_string_when_localizing:
                    matches = match_localized_txt.findall(line)
                    if len(matches) > 0:
                        term = ''
                        newline = line
                        for match in matches:
                            str_msgctxt = match[13:18]
                            p = podict.has_msgctxt(str_msgctxt)
                            if p[0]:
                                term += '[' + p[1] + '] '
                        if match_tag_comment.search(newline):
                            term = '# @' + term
                            newline2 = match_tag_comment.sub(term, newline)
                            newline = newline2
                        else:
                            newline = line[0:int(len(line)-1)]
                            newline += '  # @' + term + '\n'
                        pyout.write(newline)
                    else:
                        pyout.write(line)
                else:
                    pyout.write(line)
        pyout.close()
        pyin.close()
    except Exception, e:
        l = traceback.format_exc()
        pass


def main():
    output_root_dir = os.path.join(root_directory_to_scan, 'localized')
    if not os.path.exists(output_root_dir):
        os.makedirs(output_root_dir)
    output_po_dir = os.path.join(output_root_dir, 'resources', 'language', 'English')
    if not os.path.exists(output_po_dir):
        os.makedirs(output_po_dir)
    outputfnpofull = os.path.join(output_po_dir, 'strings.po')
    if os.path.exists(outputfnpofull):
        os.remove(outputfnpofull)
    files_to_scan = []
    exclusions = []
    for direct in exclude_directories:
        for root, dirname, filenames in os.walk(os.path.join(root_directory_to_scan, direct)):
            for filename in filenames:
                exclusions.append(os.path.join(root, filename))
    for root, dirnames, filenames in os.walk(root_directory_to_scan):
        for filename in fnmatch.filter(filenames, '*.py'):
            x = os.path.relpath(root, root_directory_to_scan)
            if os.path.split(filename)[1] in exclude_files:
                continue
            elif os.path.join(root, filename) in exclusions:
                continue
            else:
                if x != '.':
                    outpath = os.path.join(output_root_dir, x)
                    if not os.path.exists(outpath):
                        os.makedirs(outpath)
                else:
                    outpath = output_root_dir
                files_to_scan.append([os.path.join(root, filename), os.path.join(outpath, filename)])

    global podict
    podict = PoDict()
    podict.read_from_file(current_working_English_strings_po)

    for mfile in files_to_scan:
        inputfnfull = mfile[0]
        outputfnpyfull = mfile[1]
        if os.path.exists(outputfnpyfull):
            os.remove(outputfnpyfull)
        pyin = open(inputfnfull, 'r')
        pyout = open(outputfnpyfull, 'w')
        try:
            examinefile(pyin, pyout)
        except Exception, e:
            l = traceback.format_exc()
            pass
        pyout.close()
        pyin.close()
    podict.write_to_file(outputfnpofull)


if __name__ == '__main__':
    main()
