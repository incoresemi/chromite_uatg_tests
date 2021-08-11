=========================
Micro-Arch-Test Framework
=========================


Adding new tests
----------------

Before adding new test cases to the framework, one needs to understand
the conventions that are followed to ensure code compatibility and
automation.

Note : The ``execute``,\ ``generate_asm`` and ``check_log`` functions'
implementation are **mandatory**. The default return values are as
follows, ``execute``:``False``, ``generate_asm``:``''``,
``check_log``:``None``.

1. Packages Imported by the test\_generator

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

5. Defining the ``check_log`` function:

   1. Read the log file from ``log_file_path`` variable.
   2. Using the regex patterns given from the ``regex_formats.py`` file,
      and ``re`` module, parse the log file.
   3. Create conditions that test for successful execution and fail
      cases.
   4. If the assembly test passes, return ``True`` else return
      ``False``.

6. If the ``regex-formats.py`` file does not have suitable regex
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

      def check_log(self, log_file_path):

        """ Docstring for check_log, this function checks whether the Device under Test (DUT) has executed appropriately"""
        if self.execute(log_file_path):
             f = open(log_file_path, "r")  # Reading the file from given path
             log_file = f.read()
             f.close()

             # parse the log file, extract the needed patterns.
             # based on the occurrences and frequency validate the execution
             ghr_update_result = re.findall(rf.ghr_update_pattern, log_file)

             # design your own conditions based on the need and return True if test has passed
             if len(ghr_update_result) != 8:
               return False  # Return False if test has failed.
             return True  # Return True if test has passed.
        return None # To denote that test-case was not implemented/tested


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

