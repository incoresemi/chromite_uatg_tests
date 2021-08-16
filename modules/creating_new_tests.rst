.. _creating_new_tests: 

=========================
Micro-Arch-Test Framework
=========================


Adding new tests
----------------

Before adding new test cases to the framework, one needs to understand
the conventions that are followed to ensure code compatibility and
automation.

Note : The ``execute``, ``generate_asm``, ``generate_covergroups`` and ``check_log`` functions'
implementation are **mandatory**. The default return values are as
follows, ``execute``:``False``, ``generate_asm``:``''``, ``generate_covergroups``:``''``,
``check_log``:``None``.

1. Packages Imported by the test_generator

   1. Yapsy: for plugin management (version>=1.12.2)
   2. regex\_formats: file containing regex expressions for commonly
      used log patterns ()
   3. re: python regular expression library

2. Creating a class with same name as that of the test\_name and
   initializing with default parameters that is needed for generating
   the assembly program.

3. Defining the ``execute`` function:

   1. This function returns if the current DUT configuration has the
      necessary hardware implemented for this(new test to be added) test
      to be run on.
   2. Obtain the requisite parameters from the DUT configuration yaml
      file and check if the test should be generated. An example
      parameter could be 'btbdepth' in the case of a 'gshare BPU'. It is
      recommended that the user checks if the hardware unit would be
      **instantiated** before moving on to other cases.
   3. If the requisite hardware is implemented return ``True`` else
      return ``False``

4. Defining the ``generate_asm`` function:

   -  This function should return a formatted string. This string will
      be directly written as the assembly test program.

5. Defining the ``generate_covergroups`` function:
   
   - This function should return a formatted string of the SV coverpoints which the user 
     expects to get covered in their test. This string will be directly written into an SV file.

6. Defining the ``check_log`` function:

   1. Read the log file from ``log_file_path`` variable.
   2. Using the regex patterns given from the ``regex_formats.py`` file,
      and ``re`` module, parse the log file.
   3. Create conditions that test for successful execution and fail
      cases.
   4. If the assembly test passes, return ``True`` else return
      ``False``.
   5. The reports dir will contain the path where the reports from the check log 
      would be created.

7. If the ``regex-formats.py`` file does not have suitable regex
   patterns, frame the regex pattern and store it in the file with
   suitable naming.

A generic test ``test_name.py`` is written in this manner. This test
uses the parameters from the Chromite's default configuration. We write
a test for the BPU here. The user should modify this test accordingly to
suite their needs.

.. code:: python

    """Docstring for the test explaining the objective and results"""

    from yapsy.IPlugin import IPlugin
    import regex_formats as rf  # file containing regex_patterns useful for log parsing
    import re

    class test_name(IPlugin):

      def __init__(self):
        super().__init__()
        self.parameter_name1 = 5  # initialize the internal parameters needed for the script
        self.parameter_name2 = None

      def execute(self, _bpu_dict):
        """ Docstring explaining the rationale behind why the test was created or not based on the chosen parameters"""
        # _block_parameters( in this case _bpu_dict) are the details of the configuration of a particular block given as a dictionary
        ras_depth = _bpu_dict['ras_depth']
        # obtain the needed external parameters from the input dictionary
        _bpu_enabled = _bpu_dict['instantiate']

        # IMPORTANT: check for conditions in which the test needs to be generated
        if ras_depth >= 1 and _bpu_enabled:
          return True
        else:
          return False

      def generate_asm(self):

        """ Docstring for the generate_asm method explaining the asm code's details"""
        """ Registers used and their functions, instructions called and their purposes etc"""

        recurse_level = self.parameter_name1
        asm = "assembly code to be generated in terms of string"
        return asm  # generate_asm returns the assembly code as a string
      
      def generate_covergroups(self, config_file):
        
        """ Generates SV covergroups """
        sv = ""
        sv += "enter SV covergroup syntax here"
        return (sv)

      def check_log(self, log_file_path, reports_dir):

        """ Docstring for check_log, this function checks whether the Device under Test (DUT) has executed appropriately"""
        """
          check if all the ghr values are zero throughout the test
        """
        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()
        test_report = {
            "gshare_fa_ghr_zeros_01_report": {
                'Doc': "ASM should have generated 00000... pattern in the GHR "
                       "Register. This report show's the "
                       "results",
                'expected_GHR_pattern': None,
                'executed_GHR_pattern': None,
                'Execution_Status': None
            }
        }
        test_report['gshare_fa_ghr_zeros_01_report'][
            'expected_GHR_pattern'] = '0' * self._history_len
        res = None
        alloc_newind_pattern_result = re.findall(rf.alloc_newind_pattern,
                                                 log_file)
        ghr_patterns = [
            i[-self._history_len:] for i in alloc_newind_pattern_result
        ]
        for i in ghr_patterns:
            if self._history_len * '0' in i:
                test_report['gshare_fa_ghr_zeros_01_report'][
                    'executed_GHR_pattern'] = i
                test_report['gshare_fa_ghr_zeros_01_report'][
                    'Execution_Status'] = 'Pass'
                res = True
                break
            else:
                res = False
        if not res:
            test_report['gshare_fa_ghr_zeros_01_report'][
                'executed_GHR_pattern'] = ghr_patterns
            test_report['gshare_fa_ghr_zeros_01_report'][
                'Execution_Status'] = 'Fail: expected pattern not found'

        f = open(
            os.path.join(reports_dir, 'gshare_fa_ghr_zeros_01_report.yaml'),
            'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()

        return res



Framework Structure
-------------------

The framework is structured in the following manner.

-  New folders are to be created for each block that needs to be tested
   (e.g. ``bpu/``).
-  Within each block's folder, a ``tests/`` folder is created to store
   the generated assembly codes. In addition, the python scripts to
   automate the assembly file generation are stored in the block's
   folder.
-  For automating the test generating process, we are using ``yapsy``
   module which needs a plugin file (e.g. ``test_no_1.yapsy-plugin``)
   created for each python script. To avoid hassle, we have automated
   the process of creating the plugin files too. The plugin files are
   created when ``test_generator.py`` is called. The plugin files are
   ignored by git.
-  The ``test-generator.py`` script parses through all the tests defined
   in the block folder and chooses specific tests based on their
   applicability (more about this in the ``Adding new tests`` section).
-  For each chosen test case, the script creates new folders with the
   test name inside the ``tests/`` folder and writes assembly files into
   each of the respective folders.

.. code:: shell

    framework/
    ├── bpu
    │    ├── test_01.py
    │    ├── *test_01.yapsy-plugin
    │    ├── test_02.py
    │    ├── *test_02.yapsy-plugin
    │    ├── ...
    │    ├── ...
    │    ├── test_n.py
    │    ├── *test_n.yapsy-plugin
    │    └── tests
    │        ├── test_01
    │        │    ├── test_01.S
    │        │    ├── log
    │        │    └── ...
    │        ├── test_02
    │        │    ├── test_02.S
    │        │    ├── log
    │        │    └── ...
    │        │    ...
    │        │    ...
    │        └── test_m
    │             ├── test_m.S
    │             ├── log
    │             └── ...
    ├── ...
    ├── README.md
    ├── regex_formats.py
    └── test_generator.py

