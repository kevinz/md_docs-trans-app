#!/usr/bin/env python3
import os
import sys
import re
import argparse
import unicodedata

def replace_in_file(file_path, convert):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        md_text = ''.join(lines)
    print("Processing file: ", file_path)
    if not lines:
        return
    sep_search_scope = 10
    first_sep_line = 0 if lines[0].startswith("---") else None
    last_sep_line = None

    # deal with meta header
    # keepr means keep&remove
    if first_sep_line is not None:
        for i in range(first_sep_line + 1, len(lines[:sep_search_scope])):
            if ':' in lines[i]:
                left, right = lines[i].split(':', 1)
                # lines[i] = f'<keepr>{left}:</keepr>{right}'
            if lines[i].startswith("---"):
                last_sep_line = i
                break
    # convert  
    if convert:
        meet_begin_ident_code_block = False
        meet_begin_table_block = False

        # deal with meta header last seperator, add new line before the seperator
        if last_sep_line:
            lines.insert(last_sep_line, '\n')

        for i, line in enumerate(lines):
            # deal with import
            if line.startswith("import ") and (line.strip().endswith(".mdx'") or line.strip().endswith(".md'") or line.strip().endswith("\"") or line.strip().endswith(";") ) :
                lines[i] = '<keepimp>' + line.strip() + '</keepimp>\n'

            # deal with hugo {{}}
            lines[i] = lines[i].replace('{{', '<keep>').replace('}}', '</keep>')
            # deal with img and links
            if ("![" in lines[i] or "[" in lines[i]) and "](" in lines[i]:
                lines[i] = lines[i].replace("[","<keepr>[").replace(")", ")</keepr>")

            # deal with ident code block,bypassing the processed one            
            if '```' in line and not line.startswith('```') and not meet_begin_ident_code_block and not (lines[i-1] == '<keepr>\n' or lines[i+1] == '</keepr>\n'):
                meet_begin_ident_code_block = True
                lines.insert(i, '<keepr>\n')
                # search for the end of the code block
                for j in range(i, len(lines)):
                    if lines[j].strip() == '```' and not lines[j].startswith('```') and meet_begin_ident_code_block:
                        lines.insert(j+1, '</keepr>\n')
                        meet_begin_ident_code_block = False
                        break
            
            # deal with mardown table
            if line.startswith('| ---') and not lines[i-2] == '<keepr>\n' :
                print("table found lines[i-3]",lines[i-3])
                print("table found lines[i-2]",lines[i-2])

                lines.insert(i-1, '<keepr>\n')
                # search for the end of the code block
                table_ends_at = None
                for j in range(i, len(lines)):
                    if not lines[j].startswith('| ') or not lines[j].strip('\n').endswith(' |'):
                        print('found table ends',j,lines[j])
                        table_ends_at = j
                        break
                if table_ends_at:
                    lines.insert(table_ends_at, '</keepr>\n')

            # deal with tip tag in port docs
            if lines[i].startswith(":::tip"):
                lines[i] = lines[i].replace(':::tip','<keepr>:::tip </keepr>')
            elif lines[i].startswith(":::info"):
                lines[i] = lines[i].replace(':::info','<keepr>:::info </keepr>')
            elif lines[i].startswith(":::warning"):
                lines[i] = lines[i].replace(':::warning','<keepr>:::warning </keepr>')
            elif lines[i].startswith(":::danger"):
                lines[i] = lines[i].replace(':::danger','<keepr>:::danger </keepr>')
            elif lines[i].startswith(":::caution"):
                lines[i] = lines[i].replace(':::caution','<keepr>:::caution </keepr>')
            elif lines[i].startswith(":::note"):
                lines[i] = lines[i].replace(':::note','<keepr>:::note </keepr>')
            elif lines[i].startswith(":::important"):
                lines[i] = lines[i].replace(':::important','<keepr>:::important </keepr>')
            elif lines[i].startswith(":::attention"):
                lines[i] = lines[i].replace(':::attention','<keepr>:::attention </keepr>')
            elif lines[i].startswith(":::") and lines[i].strip() == ":::":
                lines[i] = '\n<keepr>' + lines[i].rstrip() + '</keepr>\n'
    # revert
    else:
        # fix the meta header tit,should reverse left and right
        # example:
        #脚手架新服务<keepr>title:</keepr>
        # if last_sep_line:
        #     for i, line in lines[0:last_sep_line]:
        #         if not line.startswith('<keepr>'):
        #             left, right = lines[i].split('<keepr>', 1)
        #             lines[i] = '{right} {left}'

        if not first_sep_line == None and not last_sep_line == None:
            # del newline in meta header
            if lines[last_sep_line - 1 ] == '\n':
                del lines[last_sep_line - 1]

            if lines[first_sep_line + 1 ] == '\n':                
                del lines[first_sep_line+1]
            for i in range(first_sep_line , last_sep_line):
                if ': ' in lines[i]:
                    left, right = lines[i].split(': ', 1)
                    if right.strip().isdigit():
                        continue
                    # right = ''.join(c for c in right if not unicodedata.category(c).startswith('So'))
                    lines[i] = left +": "+''+right.strip('"')+'\n'

                
        for i, line in enumerate(lines):
            lines[i] = lines[i].replace('</keepr><keepr>','\n')
            # fix space been eaten in listitem
            lines[i] = lines[i].replace('*<keepr>','* ')
            lines[i] = lines[i].replace('<keep>', '{{').replace('</keep>', '}}').replace('<keepimg>','![').replace('</keepimg>',']').replace('<keepimp>','').replace('</keepimp>','')
            # lines[i] = lines[i].replace('<keepr>\n', '\n').replace('</keepr>\n', '\n')
            lines[i] = lines[i].replace('<keepr>', '').replace('</keepr>', '')
            # convert Chinese to English
            lines[i] = lines[i].replace('：',': ')
            lines[i] = lines[i].replace('（','(').replace('）',')')
            # handle port doc with lots of <detail><summary> tag 
            if '<details>' in lines[i] and not lines[i].strip().startswith('<details>'):
                lines[i] = lines[i].replace('<details>','\n<details>')
            if '<details>' in lines[i] and not lines[i].strip('\n').endswith('<details>'):
                lines[i] = lines[i].replace('<details>','<details>\n')

            if '</details>' in lines[i] and not lines[i].strip().startswith('</details>'):
                lines[i] = lines[i].replace('</details>','\n</details>')
            if '</details>' in lines[i] and not lines[i].strip('\n').endswith('</details>'):
                lines[i] = lines[i].replace('</details>','</details>\n')

            # deal with _italic_
            # pattern = r"(_\w+?_)"
            # lines[i] = re.sub(pattern, r" \1 ", lines[i])
                

    with open(file_path, 'w') as file:
        file.writelines(lines)


def scan_directory(path, convert):
    if os.path.isdir(path):
        for foldername, subfolders, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith('.md'):
                    replace_in_file(os.path.join(foldername, filename), convert)
    else:
        if path.endswith('.md'):
            replace_in_file(path, convert)

parser = argparse.ArgumentParser(description='Scan a directory and replace "---" and "{{}}" in .md files.')
subparsers = parser.add_subparsers()

convert_parser = subparsers.add_parser('convert', help='Convert "---" to "<keep>" and "{{}}" to "</keep>"')
convert_parser.add_argument('path', help='The path to the directory to scan')
convert_parser.set_defaults(func=lambda args: scan_directory(args.path, True))

revert_parser = subparsers.add_parser('revert', help='Revert "<keep>" to "---" and "</keep>" to "{{}}"')
revert_parser.add_argument('path', help='The path to the directory to scan')
revert_parser.set_defaults(func=lambda args: scan_directory(args.path, False))

args = parser.parse_args()

if hasattr(args, 'func'):
    args.func(args)
else:
    print("Error: No command provided. Use 'convert' or 'revert'.", file=sys.stderr)
    sys.exit(1)
