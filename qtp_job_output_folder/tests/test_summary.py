# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from tempfile import mkdtemp
from os import remove
from os.path import exists, isdir, join, dirname, abspath
from inspect import currentframe, getfile
from shutil import rmtree, copytree
from json import dumps

from qiita_client.testing import PluginTestCase

from qtp_job_output_folder import __version__
from qtp_job_output_folder.summary import generate_html_summary


class SummaryTests(PluginTestCase):
    def setUp(self):
        self.out_dir = mkdtemp()
        self.source_dir = join(mkdtemp(), 'test_data')
        source = join(dirname(abspath(getfile(currentframe()))), 'test_data')
        copytree(source, self.source_dir)
        self._clean_up_files = [self.out_dir]

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_summary(self):
        files = [(self.source_dir, 'directory')]
        data = {'filepaths': dumps(files), 'type': 'job-output-folder',
                'name': "A name", 'data_type': 'Job Output Folder'}
        aid = self.qclient.post('/apitest/artifact/', data=data)['artifact']
        parameters = {'input_data': aid}
        data = {'command': dumps(['qtp-job-output-folder', __version__,
                                  'Generate HTML summary']),
                'parameters': dumps(parameters),
                'status': 'running'}
        job_id = self.qclient.post(
            '/apitest/processing_job/', data=data)['job']

        # Run the test
        obs_success, obs_ainfo, obs_error = generate_html_summary(
            self.qclient, job_id, parameters, self.out_dir)

        # asserting reply
        self.assertTrue(obs_success)
        self.assertIsNone(obs_ainfo)
        self.assertEqual(obs_error, "")

        # asserting content of html
        res = self.qclient.get("/qiita_db/artifacts/%s/" % aid)
        # cleaning artifact files, to avoid errors
        [self._clean_up_files.extend(f) for f in res['files'].values()]
        html_fp = res['files']['html_summary'][0]
        af = dirname(html_fp)
        self._clean_up_files.append(html_fp)
        with open(html_fp) as html_f:
            html = html_f.read()

        print('=========')
        print('=========')
        print(html)
        print('=========')
        print(EXP_HTML.format(af=af))
        print('=========')

        self.assertEqual(html, EXP_HTML.format(af=af))


EXP_HTML = (
    '<a href="{af}/test_data/file_2" type="file" target="_blank">{af}/'
    'test_data/file_2</a><br/>\n'
    '<a href="{af}/test_data/test_data" type="folder" target="_blank">{af}/'
    'test_data/test_data</a><br/>\n'
    '<a href="{af}/test_data/test_data/folder_a/folder_b" type="folder" '
    'target="_blank">{af}/test_data/test_data/folder_a/folder_b</a><br/>\n'
    '<a href="{af}/test_data/test_data/folder_a/folder_b/folder_c/file_c" '
    'type="file" target="_blank">{af}/test_data/test_data/folder_a/folder_b/'
    'folder_c/file_c</a><br/>\n'
    '<a href="{af}/test_data/test_data/folder_a/file_a" type="file" '
    'target="_blank">{af}/test_data/test_data/folder_a/file_a</a><br/>\n'
    '<a href="{af}/test_data/file_1" type="file" target="_blank">{af}/'
    'test_data/file_1</a><br/>\n'
    '<a href="{af}/test_data/folder_a" type="folder" target="_blank">{af}/'
    'test_data/folder_a</a><br/>\n'
    '<a href="{af}/test_data/folder_a/folder_b/folder_c" type="folder" '
    'target="_blank">{af}/test_data/folder_a/folder_b/folder_c</a>')


if __name__ == '__main__':
    main()
