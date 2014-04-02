import os
import sys

__author__ = 'anna'

class RedirectDescriptor(object):
    desc_backup = None

    def redirect_C_stderr_null(self):
        sys.stderr.flush()                                  # flush all data
        new_desc = os.dup(sys.stderr.fileno())              # create new descriptor from original stderr (copy)
        self.desc_backup = new_desc                         # save descriptor number
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stderr.fileno())               # redirect C layer descriptor to null
        os.close(devnull)
        sys.stderr = os.fdopen(new_desc, 'w')               # but revert Python stderr to normal

    def redirect_C_stderr_back(self):
        assert self.desc_backup is not None
        sys.stderr.flush()
        os.dup2(self.desc_backup, 2)
        sys.stderr = os.fdopen(2, 'w')
