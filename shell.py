git_release_tag = 'latest'
git_commit_hash = 'latest'
git_commit_date = None

import platform
import mathscript
import argparse
import difflib
import sys

def main():
	arg_parser = argparse.ArgumentParser(description=f"{mathscript.product_name} - {mathscript.product_description}", add_help=False)
	arg_group1 = arg_parser.add_mutually_exclusive_group()
	arg_group2 = arg_parser.add_argument_group()
	arg_group1.add_argument("-h", "--help", action="help", help="Show this help message and exit.")
	arg_group1.add_argument("-V", "--version", action="store_true", help=f"Display the version information of {mathscript.product_name}.")
	arg_group2.add_argument("--debug", help=f"Enable debug mode. Choose one of {mathscript.debug_modes_list_str}.", metavar="debug_mode")
	arg_group2.add_argument("file", help=f"Execute a .mscr file", nargs='?')
	arg_parser._positionals.title = "Positional arguments"
	arg_parser._optionals.title = "Optional arguments"

	args = arg_parser.parse_args()

	if args.version and (args.debug or args.file):
		if args.debug:
			arg_parser.error(f"argument -V/--version: not allowed with argument --debug")
		elif args.file:
			arg_parser.error(f"argument -V/--version: not allowed with argument file")

	if args.version:
		print(f"{mathscript.product_name} v{mathscript.version_str}")
		sys.exit()

	if args.debug:
		if args.debug in mathscript.debug_modes_list:
			mathscript.debug_mode = args.debug
		else:
			suggest = difflib.get_close_matches(args.debug, mathscript.debug_modes_list, n=1)
			print(f"Invalid debug mode specified: '{args.debug}'.{f" Did you mean '{suggest[0]}'?" if len(suggest) > 0 else ''}\nChoose from: \n\t- {'\n\t- '.join(mathscript.debug_modes_list)}")
			sys.exit()

	if args.file:
		text = ''
		with open(args.file, 'r') as f:
			text = f.read()
		try:
			result, error = mathscript.run(args.file, text)
			if error: print(error.as_string())
		except KeyboardInterrupt:
			sys.exit()
	else:
		print(f"{mathscript.product_name} v{mathscript.version_str}{f'[DEBUG:{args.debug.upper().replace('-', '_')}]' if mathscript.debug_mode != False else ''} (tags/{git_release_tag}:{git_commit_hash}{', ' + git_commit_date if git_commit_date else ''}) on {platform.system()} {platform.win32_ver()[0] if platform.system() == 'Windows' else '\b'} [Version {platform.version()}].")
		
		while True:
			try:
				text = input(f'({mathscript.product_name}) >>> ')
			except KeyboardInterrupt:
				print()
				sys.exit()
			
			result, error = mathscript.run("<stdin>", text)

			if error: print(error.as_string())
			elif result is not None:
				rst = [repr(x) for x in result.elements if x is not None]
				if len(result.elements) == 1 and result.elements[0] is not None:
					print(repr(result.elements[0]))
				elif len(rst) == 0: pass
				else: print('\n'.join(rst))

if __name__ == '__main__':
	main()