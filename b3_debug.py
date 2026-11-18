# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #


__author__  = 'GrosBedo'
__version__ = '0.8'

import b3.run
import argparse

from b3_run import *
from b3.tools.debug.functionprofiler import *
from b3.tools.debug.memoryprofiler import *


def parse_cmdline_args():
    # initializing variables
    #currdateprofile = os.path.join(pathname, '%s.profile' % str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    cancontinue = True # define if b3 can continue to run normally or not

    # initializing the arguments parser
    parser = argparse.ArgumentParser(conflict_handler='resolve', add_help=False, usage='%(prog)s [debugoptions]', description='B3 DEBUG MODE: Switch to some special debug functionnalities.', epilog='Note: for the profile to be saved, you need to wait the end of the runtime that the profile ends by itself (do not close b3 !)')
    #parser.add_argument('--help', '-h', dest='help', action='store_true', default=False, help='show this help message and exit')
    parser.add_argument('--debughelp', '-debughelp', '--debug', '-debug', dest='debughelp', action='store_true', default=False, help='show this help message and exit')
    parser.add_argument('--memory', '-m', dest='memory', action='store_true', default=False, help='activate the memory monitor')
    parser.add_argument('--memorysave', '-msave', dest='memorysave', action='store', default=None, type=str, metavar='/dir/memory.profile', help='store the memory profile to the specified file')
    parser.add_argument('--memoryload', '-mload', dest='memoryload', action='store', default=None, type=str, metavar='/dir/memory.profile', help='load a memory profile from the specified file')
    parser.add_argument('--memorydraw', '-mdraw', dest='memorydraw', action='store_true', default=False, help='draw an interactive GUI chart for the loaded memory profile')
    parser.add_argument('--memoryinteractive', '-mi', dest='memoryinteractive', action='store_true', default=False, help='draw an interactive console terminal _while_ the application is running')
    parser.add_argument('--profile', '-p', dest='profile', action='store_true', default=False, help='activate the functions profiler')
    parser.add_argument('--profilesave', '-psave', dest='profilesave', action='store', default=None, type=str, metavar='/dir/some.profile', help='store the generated profile to the specified file')
    parser.add_argument('--profileload', '-pload', dest='profileload', action='store', default=None, type=str, metavar='/dir/some.profile', help='load a profile from the specified file')
    parser.add_argument('--profiledraw', '-pdraw', dest='profiledraw', action='store_true', default=False, help='draw an interactive GUI chart for the loaded profile')
    parser.add_argument('--profiledrawnogui', '-pdraw2', dest='profiledrawnogui', action='store_true', default=False, help='draw an interactive console interface to analyze the loaded profile')
    parser.add_argument('--profilesavestats', '-pstats', dest='profilesavestats', action='store', default=None, type=str, metavar='/dir/somefile.txt', help='parse and save some stats from the loaded profile')
    parser.add_argument('--profileruntime', '-ptime', dest='profileruntime', action='store', default=60, type=float, metavar='seconds', help='time to run the profile test (the program will be stopped after)')
    parser.add_argument('--debugverbose', '-dv', dest='verbose', action='store_true', help='verbose option, output more informations on screen')

    # parsing (loading) the arguments
    try:
        args, extras = parser.parse_known_args() # We parse only the special commandlines parameter here, for the rest, the normal switchs, we give them up to the rest of B3 functions (namely the main() in b3/run.py). The recognized args are stored in args var, for the rest it's stored in extras var
        extras.insert(0, sys.argv[0]) # add the path to this script file (to normalize the arguments)
        sys.argv = extras # trim out the debug vars we will process here, so that b3 can parse the arguments normally
    except BaseException, e:
        print('Exception: %s' % str(e))
        return

    # processing the arguments
    if args.debughelp: # debug help message
        parser.print_help()
        return False

    # profiling functionnalities
    if args.memory:
            print('MEMORY PROFILER MODE\n--------------------\n')
            if args.memorysave:
                    runmemoryprofile(args.memorysave)
            if args.memoryload:
                    if args.memorydraw:
                            memorygui(args.memoryload)
            if args.memoryinteractive:
                    memoryinteractive()
            cancontinue = False

    # profiling functionnalities
    if args.profile:
        print('FUNCTIONS PROFILER MODE\n--------------------\n')
        if args.profilesave:
            runprofile("""main()""", args.profilesave, args.profileruntime)
        if args.profileload:
            if args.profiledraw:
                browseprofilegui(args.profileload)
            if args.profilesavestats:
                parseprofile(args.profileload, args.profilesavestats)
            if args.profiledrawnogui:
                browseprofile(args.profileload)
        cancontinue = False

    return cancontinue


def main():
    b3.run.main()

if __name__ == '__main__':
    result = parse_cmdline_args() # we parse here for special debug switchs, if there are none, the program will continue normally
    if result: # result will be False if we launched the profiler, or any function that should activate a special behaviour that could conflict with the normal main function
        main()