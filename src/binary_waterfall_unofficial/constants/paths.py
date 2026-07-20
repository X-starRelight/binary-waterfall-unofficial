import os
import sys

# Test if this is a PyInstaller executable or a .py file
if getattr(sys, 'frozen', False):
    IS_EXE = True
    PATH = os.path.join(sys._MEIPASS, os.path.sep.join(__name__.split(".")[:-2])) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportAttributeAccessIssue]
else:
    IS_EXE = False # pyright: ignore[reportConstantRedefinition]
    PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) # pyright: ignore[reportConstantRedefinition]
