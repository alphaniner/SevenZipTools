from fman import submit_task, show_alert, show_prompt, DirectoryPaneCommand, \
                  Task, ABORT, CANCEL, NO, PLATFORM, YES
from fman.fs import exists, is_dir, mkdir, move_to_trash, resolve
from fman.url import as_human_readable, join, splitscheme

from .configuration import _CHECK_EXTENSION, _COMPARE_HASH, _COMPRESS_ARGS, \
                            _HASH, _SUPPORTED_EXTENSIONS, _USER_7ZIP

from os import name as osname
from os.path import basename

import core.fs.zip

import re
import subprocess

_FMAN_7ZIP = core.fs.zip._7ZIP_BINARY

class _7zipTaskWithProgress(Task):
    def run_7zip_with_progress(self, args, **kwargs):
        if _USER_7ZIP:
            core.fs.zip._7ZIP_BINARY = _USER_7ZIP
        with core.fs.zip._7zip(args, pty=True, **kwargs) as process:
            for line in process.stdout_lines:
                try:
                    self.check_canceled()
                except Task.Canceled:
                    # It's necessary to reset the binary if it was changed.
                    if _USER_7ZIP:
                        core.fs.zip._7ZIP_BINARY = _FMAN_7ZIP
                    process.kill()
                    raise
                # The \r appears on Windows only:
                match = re.match('\r? *(\\d\\d?)% ', line)
                if match:
                    percent = int(match.group(1))
                    # At least on Linux, 7za shows progress going from 0 to
                    # 100% twice. The second pass is much faster - maybe
                    # some kind of verification? Only show the first round:
                    if percent > self.get_progress():
                        self.set_progress(percent)
        # It's necessary to the binary if it was changed.
        if _USER_7ZIP:
            core.fs.zip._7ZIP_BINARY = _FMAN_7ZIP

class ExtractArchive(_7zipTaskWithProgress):
    def __init__(self, zip_path, dest_path):
        super().__init__('Extracting ' + basename(zip_path), size=100)
        self._zip_path = zip_path
        self._dest_path = '-o' + dest_path
    def __call__(self):
        args = ['x', self._zip_path, self._dest_path]
        self.run_7zip_with_progress(args)

class ExtractToOpposite(DirectoryPaneCommand):
    def __call__(self, url=None):

        # This will get set if the automagically determined destination
        #  directory exists, and will always be the default name when prompted
        #  to manually choose a destination directory name.
        originalName = None

        if url is None:
            workingFile = self.pane.get_file_under_cursor()
            if workingFile:
                url = workingFile

        fileName = basename(url)

        if _CHECK_EXTENSION:

            try:
                extension = fileName[fileName.rindex('.'):]
            except ValueError:
                show_alert("Failed to determine extension, aborting!")
                return

            if not extension in _SUPPORTED_EXTENSIONS:
                show_alert("Unsupported extension, aborting!")
                return

            newDirName = fileName[0:fileName.rindex('.')]

        else:

            try:
                newDirName = fileName[0:fileName.rindex('.')]

            except ValueError:

                message = "Archive has no extension.\n"
                message += "Click 'YES' to enter a name "
                message += "for the destination directory.\n"
                message += "Click 'NO' to use the archive name.\n"
                message += "Click 'ABORT' to abort extraction."

                choice = show_alert(message, buttons = YES | NO | ABORT,
                                    default_button = ABORT)

                if choice == YES:
                    newDirName, ok = show_prompt("Destination directory:",
                                                 default=fileName)
                    if not (newDirName and ok):
                        return

                elif choice == NO:
                    newDirName = fileName

                else:
                    return

        oppositePane = _get_opposite_pane(self.pane)
        oppositePaneUrl = oppositePane.get_path()
        oppositePaneScheme, _ = splitscheme(resolve(oppositePaneUrl))
        if oppositePaneScheme != 'file://':
            show_alert("Can't extract to %s, aborting!" % oppositeScheme)
            return

        newDirUrl = join(oppositePaneUrl, newDirName)

        while exists(newDirUrl):
            if not originalName:
                originalName = newDirName
            message = newDirName + " already exists!\nEnter a different name?"
            choice = show_alert(message, buttons = YES | ABORT,
                                default_button = ABORT)
            if choice == YES:
                newDirName, ok = show_prompt("Destination directory:",
                                                 default=newDirName)
                if not (newDirName and ok):
                    continue
                else: newDirUrl = join(oppositePaneUrl, newDirName)

        try:
            mkdir(newDirUrl)
        except (FileNotFoundError, NotImplementedError):
            message = "Failed to create directory '"
            message += newDirName + "', aborting!"
            show_alert(message)
            return

        archive = as_human_readable(url)
        destDir = as_human_readable(newDirUrl)

        submit_task(ExtractArchive(archive, destDir))

        return

class CreateArchive(_7zipTaskWithProgress):
    def __init__(self, zip_path, src_path):
        super().__init__('Compressing ' + basename(src_path), size=100)
        self._zip_path = zip_path
        self._cwd = src_path
    def __call__(self):
        args = _COMPRESS_ARGS + [self._zip_path, '.']
        self.run_7zip_with_progress(args, cwd=self._cwd)

class CompressToOpposite(DirectoryPaneCommand):
    def __call__(self, url=None):

        sourceDirUrl = self.pane.get_path()
        archiveName = basename(sourceDirUrl) + '.7z'

        oppositePane = _get_opposite_pane(self.pane)
        oppositePaneUrl = oppositePane.get_path()

        archiveUrl = join(oppositePaneUrl, archiveName)

        sourceDir = as_human_readable(sourceDirUrl)
        archive = as_human_readable(archiveUrl)

        if exists(archiveUrl):

            if is_dir(archiveUrl):
                message = archiveName + " exists and is a directory, aborting!"
                show_alert(message)
                return

            choice = show_alert("Archive exists!\nReplace?",
                                buttons = YES | CANCEL,
                                default_button = CANCEL)
            if choice == YES:
                try:
                    move_to_trash(archiveUrl)
                except NotImplementedError:
                    show_alert("Failed to delete archive, aborting!")
                    return

            elif choice == CANCEL:
                return

        submit_task(CreateArchive(archive, sourceDir))
        oppositePane.reload()

        return

class GetHash(DirectoryPaneCommand):
    def __call__(self, url=None):

        if url is None:
            workingFile = self.pane.get_file_under_cursor()
            if workingFile:
                url = workingFile

        hash = _get_hash(url, hash_type=_HASH)

        if hash:
            show_alert(hash)

        return

class CompareFiles(DirectoryPaneCommand):
    def __call__(self, url=None):

        if url is None:
            workingFile = self.pane.get_file_under_cursor()
            if workingFile:
                url = workingFile

        oppositePane = _get_opposite_pane(self.pane)
        oppositePaneUrl = oppositePane.get_file_under_cursor()

        # Considering names isn't practical when comparing directories because
        #  it results in a mismatch if only the names of the directories
        #  being compared differ.
#        if is_dir(url) and is_dir(oppositePaneUrl):
#            considerNames=True
#        else:
#            considerNames=False
        considerNames=False

        thisHash = _get_hash(url, hash_type=_COMPARE_HASH,
                             consider_names=considerNames)
        thatHash = _get_hash(oppositePaneUrl, hash_type=_COMPARE_HASH,
                             consider_names=considerNames)

        if thisHash == thatHash:
            show_alert("Files match.")
        else:
            show_alert("Files differ.")

        return

def _get_hash(url, hash_type='crc32', consider_names=False):
    # Valid values for hash_type: crc32, crc64, sha1, sha256, blake2sp

    startupinfo = None
    if osname == u'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # Considering names isn't practical when comparing directories because
    #  it results in a mismatch if only the names of the directories
    #  being compared differ.
#    if consider_names:
#        regHashSearch = re.compile(r'and names:', re.U).search
#        hashIndex = 5
#    else:
#        regHashSearch = re.compile(r'for data:', re.U).search
#        hashIndex = 3
    regHashSearch = re.compile(r'for data:', re.U).search
    hashIndex = 3

    regErrMatch = re.compile(u'^(Error:.+|.+     Data Error?|Sub items Errors:.+)',
        re.U).match

    if _USER_7ZIP:
        sevenZipBinary = _USER_7ZIP
    else:
        sevenZipBinary = _FMAN_7ZIP

    workingFile = as_human_readable(url)

    command = u'"%s" h "-scrc%s" "%s"' % (sevenZipBinary,
                                          hash_type,
                                          workingFile)
    if PLATFORM == "Windows":
        command += u' -sccWIN'

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1,
                            stdin=subprocess.PIPE, startupinfo=startupinfo)
    errorLine = u''

    with proc.stdout as out:
        for line in iter(out.readline, b''):
            line = str(line, 'utf8')
            if regErrMatch(line):
                errorLine = line + u''.join(out)
                break
            if regHashSearch(line):
                dataHash = line.split()[hashIndex]

    returnCode = proc.wait()
    if returnCode or errorLine:
        show_alert(u'%s: Get hash failed:\nReturn value: %s\n%s' % (
                   basename(workingFile), str(returnCode), errorLine))
        return None
    else:
        return dataHash

def _get_opposite_pane(pane):
    panes = pane.window.get_panes()
    return panes[(panes.index(pane) + 1) % len(panes)]
