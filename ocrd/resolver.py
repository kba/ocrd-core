import os
from shutil import copyfile
import tempfile
import requests

from ocrd.constants import METS_XML_EMPTY, TMP_PREFIX, EXT_TO_MIME
from ocrd.utils import getLogger, safe_filename
from ocrd.resolver_cache import ResolverCache
from ocrd.workspace import Workspace
from ocrd.model import OcrdMets

log = getLogger('ocrd.resolver')
tempfile.tempdir = '/tmp'

class Resolver(object):
    """
    Handle Uploads, Downloads, Repository access and manage temporary directories
    Optionally cache files.

    Args:
        cache_enabled (Boolean): Whether to cache files. If True, passes kwargs to ~ResolverCache.
        prefer_symlink (Boolean): If True, symlink from cached file to the workspace instead of copying to reduce I/O.
    """

    def __init__(self, cache_enabled=False, prefer_symlink=False, **kwargs):
        """
        """
        self.cache_enabled = cache_enabled
        self.prefer_symlink = prefer_symlink
        self.cache = ResolverCache(**kwargs) if cache_enabled else None

    def _copy_or_symlink(self, src, dst, prefer_symlink=None):
        if prefer_symlink is None:
            prefer_symlink = self.prefer_symlink
        if os.path.exists(dst):
            return
        if prefer_symlink:
            os.symlink(src, dst)
        else:
            copyfile(src, dst)

    def download_to_directory(self, directory, url, basename=None, overwrite=False, subdir=None, prefer_symlink=None):
        """
        Download a file to the workspace.

        If basename is not given but subdir is, assume user knows what she's doing and use last URL segment as the basename.
        If basename is not given and no subdir is given, use the alnum characters in the URL as the basename.

        Args:
            directory (string): Directory to download files to
            basename (string, None): basename part of the filename on disk.
            url (string): URL to download from
            overwrite (boolean): Whether to overwrite existing files with that name
            subdir (boolean, None): Subdirectory to create within the directory. Think fileGrp.
            prefer_symlink (boolean): Whether to use symlinks instead of copying. Overrides self.prefer_symlink

        Returns:
            Local filename
        """
        if basename is None:
            if subdir is not None:
                basename = url.rsplit('/', 1)[-1]
            else:
                basename = safe_filename(url)

        if subdir is not None:
            basename = os.path.join(subdir, basename)

        outfilename = os.path.join(directory, basename)

        if os.path.exists(outfilename) and not overwrite:
            log.debug("File already exists and overwrite=False: %s", outfilename)
            return outfilename

        outfiledir = outfilename.rsplit('/', 1)[0]
        #  print(outfiledir)
        if not os.path.isdir(outfiledir):
            os.makedirs(outfiledir)

        cached_filename = self.cache.get(url) if self.cache_enabled else False

        if cached_filename:
            log.debug("Found cached version of <%s> at '%s'", url, cached_filename)
            self._copy_or_symlink(cached_filename, outfilename, prefer_symlink)
        else:
            log.debug("Downloading <%s> to '%s'", url, outfilename)
            if url.startswith('file://'):
                self._copy_or_symlink(url[len('file://'):], outfilename, prefer_symlink)
            else:
                with open(outfilename, 'wb') as outfile:
                    response = requests.get(url)
                    if response.status_code != 200:
                        raise Exception("Not found: %s (HTTP %d)" % (url, response.status_code))
                    outfile.write(response.content)

        if self.cache_enabled and not cached_filename:
            cached_filename = self.cache.put(url, filename=outfilename)
            log.debug("Stored in cache <%s> at '%s'", url, cached_filename)

        return outfilename

    def workspace_from_url(self, mets_url, directory=None):
        """
        Create a workspace from a METS by URL.

        Sets the mets.xml file
        """
        if directory is None:
            directory = tempfile.mkdtemp(prefix=TMP_PREFIX)
        log.debug("Creating workspace '%s' for METS @ <%s>", directory, mets_url)
        self.download_to_directory(directory, mets_url, basename='mets.xml', prefer_symlink=False)
        return Workspace(self, directory)

    def workspace_from_folder(self, directory, return_mets=False, clobber_mets=False, convention='ocrd-gt'):
        """
        Create a workspace from a folder, creating a METS file.

        Args:
            convention: See add_files_to_mets
            clobber_mets (boolean) : Whether to overwrite existing mets.xml. Default: False.
            return_mets (boolean) : Do not create the actual mets.xml file but return the :class:`OcrdMets`. Default: False.
        """
        if directory is None:
            raise Exception("Must pass directory")
        if not os.path.isdir(directory):
            raise Exception("Directory does not exist or is not a directory: '%s'" % directory)
        if not clobber_mets and os.path.exists(os.path.join(directory, 'mets.xml')):
            raise Exception("Not clobbering existing mets.xml in '%s'." % directory)

        mets = OcrdMets(content=METS_XML_EMPTY)

        if not os.path.exists(directory):
            os.makedirs(directory)
        directory = os.path.abspath(directory)

        self.add_files_to_mets(convention, mets, directory)

        if return_mets:
            return mets

        #  print(mets.to_xml(xmllint=True).decode('utf-8'))
        mets_fpath = os.path.join(directory, 'mets.xml')
        with open(mets_fpath, 'wb') as fmets:
            log.info("Writing %s", mets_fpath)
            fmets.write(mets.to_xml(xmllint=True))

        return Workspace(self, directory)

    def add_files_to_mets(self, convention, mets, directory):
        """
        Add files from folder to METS, accoding to a file structure convention.

        Args:
            convention (string) : Which file structure convention to adhere to.

                'ocrd-gt' (Default)::

                    Subfolder name ==> mets:fileGrp @USE
                        'page' => 'OCR-D-OCR-PAGE'
                        'alto' => 'OCR-D-OCR-ALTO'
                        'tei' => 'OCR-D-OCR-TEI'
                    fileGrp + '_' + upper(Basename of file without extension) == mets:file @ID
                    File in root folder == mets:fileGrp @USE == 'OCR-D-IMG'
                    Extension ==> mets.file @MIMETYPE
                        .tif => image/tif
                        .png => image/png
                        .jpg => image/jpg
                        .xml => image/xml

        """
        if convention == 'ocrd-gt':
            for root, dirs, files in os.walk(directory):
                dirname = root[len(directory):]
                if not dirname:
                    fileGrp = 'OCR-D-IMG'
                elif '/' in dirname:
                    del dirs[:]
                    fileGrp = dirname[1:].upper()
                for f in files:
                    for ext in EXT_TO_MIME:
                        if f.endswith(ext):
                            mimetype = EXT_TO_MIME[ext]
                    if dirname == '/alto':
                        mimetype = 'application/alto+xml'
                        fileGrp = 'OCR-D-OCR-ALTO'
                    elif dirname == '/page':
                        fileGrp = 'OCR-D-OCR-PAGE'
                    ID = '_'.join([fileGrp, f.replace('.', '_')]).upper()
                    local_filename = os.path.join(directory, f)
                    url = 'file://' + local_filename
                    mets.add_file(fileGrp, mimetype=mimetype, url=url, local_filename=local_filename, ID=ID)
