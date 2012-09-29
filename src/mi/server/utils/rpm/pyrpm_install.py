import os
from mi.server.utils import logger
def rpm_installcb(what, bytes, total, h, data):
    global  cur_rpm_fd
    (mia, operid) = data
    if what == rpm.RPMCALLBACK_INST_OPEN_FILE: #@UndefinedVariable
        cur_rpm_fd = os.open(h, os.O_RDONLY)
        return  cur_rpm_fd
    elif what == rpm.RPMCALLBACK_INST_CLOSE_FILE: #@UndefinedVariable
        os.close(cur_rpm_fd)
    elif what == rpm.RPMCALLBACK_INST_PROGRESS: #@UndefinedVariable
        mia.set_step(operid, bytes, total)
        

def do_ts_install():
    global ts
    if ts is None:
        logger.i('Create TransactionSet\n')
        ts = rpm.TransactionSet(CF.D.TGTSYS_ROOT)
        ts.setProbFilter(rpm.RPMPROB_FILTER_OLDPACKAGE | #@UndefinedVariable
                         rpm.RPMPROB_FILTER_REPLACENEWFILES | #@UndefinedVariable
                         rpm.RPMPROB_FILTER_REPLACEOLDFILES | #@UndefinedVariable
                         rpm.RPMPROB_FILTER_REPLACEPKG) #@UndefinedVariable
        ts.setVSFlags(~(rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSA)) #@UndefinedVariable
        
        # have been removed from last rpm version
        #ts.setFlags(rpm.RPMTRANS_FLAG_ANACONDA)
    try:
        rpmfd = os.open(pkgpath, os.O_RDONLY)
        hdr = ts.hdrFromFdno(rpmfd)
        ts.addInstall(hdr, pkgpath, 'i')
        os.close(rpmfd)
        # Sign the installing pkg name in stderr.
        print >>sys.stderr, '%s ERROR :\n' % pkgname
        problems = ts.run(rpm_installcb, (mia, operid))
        if problems:
            logger.i('PROBLEMS: %s\n' % str(problems))
            # problems is a list that each elements is a tuple.
            # The first element of the tuple is a human-readable string
            # and the second is another tuple such as:
            #    (rpm.RPMPROB_FILE_CONFLICT, conflict_filename, 0L)
            return  problems
    except Exception, errmsg:
        logger.i('FAILED: %s\n' % str(errmsg))
        return str(errmsg)
    
def pkg_post():
    global ts
    if ts is not None:
        dolog('Close TransactionSet\n')
        ts.closeDB()
        ts = None