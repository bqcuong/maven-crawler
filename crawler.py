import errno
import os
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

root_url = 'https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core'
download_folder = '~/.m2/repository/com/fasterxml/jackson/core/jackson-core'


def list_versions(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a')
            if (not node.get('href').endswith('../') and
                not node.get('href').endswith('.xml') and
                not node.get('href').endswith('.md5') and
                not node.get('href').endswith('.sha1'))]


def list_downloaded_files(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    return [url + node.get('href') for node in soup.find_all('a')
            if (node.get('href').endswith('.jar') and
                not node.get('href').endswith('javadoc.jar') and
                not node.get('href').endswith('sources.jar'))]


def download_version(version_url, dl_folder):
    version = version_url.replace(root_url, '')
    version = version.replace('/', '')
    print('-> Downloading Version: ' + version)
    folder = os.path.join(dl_folder, version)
    existed = False
    if os.path.exists(folder):
        print('Existed!')
        existed = True
    else:
        os.makedirs(folder)

    files = list_downloaded_files(version_url)
    files_info = []
    for f in files:
        file_name = os.path.basename(urlparse(f).path)
        if existed:
            files_info.append({'version': version, 'file_name': file_name})
            continue
        print('--> Downloading File:' + file_name)
        r = requests.get(f)
        with open(os.path.join(folder, file_name), 'wb') as f2:
            f2.write(r.content)
            f2.close()
        files_info.append({'version': version, 'file_name': file_name})
    return files_info

# Taken from https://stackoverflow.com/a/600612/119527
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir_p(os.path.dirname(path))
    return open(path, 'wb')


def write_file(path, content):
    with safe_open_w(path) as f:
        f.write(content)


def read_file(path):
    with open(path, 'rb') as file:
        content = file.read()
        file.close()
        return content


def copy_files(from_folder, target_folder, subject_files):
    if type(from_folder) != Path:
        from_folder = Path(from_folder)
    if type(target_folder) != Path:
        target_folder = Path(target_folder)

    for file_path in subject_files:
        print('Copy file [{0}] -> [{1}]: {2}'.format(from_folder, target_folder, file_path))


def make_snapshots(files_info, root_folder):
    for fi in files_info:
        from_folder = os.path.join(root_folder, fi['version'])
        target_folder = os.path.join(root_folder, fi['version'] + '-SNAPSHOT')
        content = read_file(os.path.join(from_folder, fi['file_name']))
        write_file(os.path.join(target_folder, fi['file_name'].replace('.jar', '-SNAPSHOT.jar')), content)
        print('Make SNAPSHOT: {0}/{1}'.format(fi['version'] + '-SNAPSHOT', fi['file_name'].replace('.jar', '-SNAPSHOT.jar')))


if __name__ == '__main__':
    versions = list_versions(root_url)
    list_files = []
    for version_url in versions:
        res = download_version(version_url, download_folder)
        list_files.extend(res)
    make_snapshots(list_files, download_folder)
