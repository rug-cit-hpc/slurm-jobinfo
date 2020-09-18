import sys
import tempfile
import unittest
import unittest.mock

def load_module_from_file(module_name, module_path):
    """Loads a python module from the path of the corresponding file.
    Args:
        module_name (str): namespace where the python module will be loaded,
            e.g. ``foo.bar``
        module_path (str): path of the python file containing the module
    Returns:
        A valid module object
    Raises:
        ImportError: when the module can't be loaded
        FileNotFoundError: when module_path doesn't exist
    """
    from importlib.machinery import SourceFileLoader
    import types
    loader = SourceFileLoader(module_name, module_path)
    loaded = types.ModuleType(loader.name)
    loader.exec_module(loaded)
    return loaded

jobinfo = load_module_from_file('jobinfo', './jobinfo')


class TestJobinfo(unittest.TestCase):
#    def test_byte_size(self):
#        self.assertEqual(self.jobinfo.None)

    def test_memory_to_bytes(self):
        self.assertEqual(jobinfo.memory_to_bytes('1Gc',  1),  1*1024**3)
        self.assertEqual(jobinfo.memory_to_bytes('1Gc', 24), 24*1024**3)
        self.assertEqual(jobinfo.memory_to_bytes('1Gn',  1),  1*1024**3)
        self.assertEqual(jobinfo.memory_to_bytes('1Gn', 24),  1*1024**3)

    @unittest.mock.patch('subprocess.Popen')
    def test_get_cpus_node(self, mock_subproc_popen):
        stdout_mock = tempfile.NamedTemporaryFile(delete=False)
        stdout_mock.write(b'   CfgTRES=cpu=24,mem=128500M,billing=24')
        stdout_mock.seek(0)
        mock_subproc_popen.return_value.stdout = stdout_mock
        self.assertEqual(jobinfo.get_cpus_node('pg-node123,pg-node124'), 24)

if __name__ == '__main__':
    unittest.main()
