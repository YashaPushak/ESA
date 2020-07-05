import inspect
import argparse
import os

import helper


class ArgumentParser:
    """ArgumentParser

    The ArgumentParser can parse command line arguements, scenario file
    arguments and global default arguments to initialize the parameters of GPS.
    """

    def __init__(self):
        self.setup_arguments = {
            ('--file-name',): {
                'help': 'The name of the file that contains the running times '
                        '(or other performance metric) of your algorithm.',
                'type': str},
            ('--alg-name', '--algorithm-name'): {
                'help': 'The name of the algorithm for '
                        'which you are performing scaling '
                        'analysis.',
                'type': str},
            ('--inst-name', '--instance-name'): {
                'help': 'The name of the instance set on '
                        'which your algorithm was evaluated.',
                'type': str},
            ('--model-file-name',): {
                'help': 'The name of the file that determines which models '
                        'are fitted to the data. This file also defines how the '
                        'models are formatted in the LaTeX report and provides '
                        'the model definitions for gnuplot.',
                'type': str},
            ('--train-test-split',): {
                'help': 'Determines how much of the data is used as the training '
                        'set and how much is used as the test set. Should be '
                        'in (0, 1).',
                'type': _validate(float, 'The train-test split must be a real '
                                         'number in (0, 1)', 
                                  lambda x: 0 < float(x) < 1)},
            ('--alpha', '--confidence-level'): {
                'help': 'The confidence level used to calculate the confidence '
                        'intervals. If less than 1, will be interpretted as '
                        '100*alpha. Must be in (0, 100)',
                'type': _validate(float, 'The confidence level (alpha) must be '
                                         'in (0, 100)', 
                                  lambda x: 0 < float(x) < 100)},
            ('--num-bootstrap-samples', '--n-bootstrap',): {
                'help': 'The number of (outer) bootstrap samples used.', 
                'type': _validate(int, 'The number of bootstrap samples must be '
                                       'at least 50', 
                                  lambda x: int(x) >= 50)},
            ('--statistic',): {
                'help': 'The statistic for which ESA should compute the scaling '
                        'of the algorithm. Supported options are "median", '
                        '"mean" and arbitrary quantiles. For example, the 95th '
                        'quantile can be selected as "q95".',
                'type': str},
            ('--latex-template',): {
                'help': 'The name of the LaTeX template to use when generating '
                        'the automated technical report pdf document.',
                'type': str},
            ('--residue-plot-template',): {
                'help': 'The name of the gnuplote templateto use for plotting '
                        'the residues of the fitted models.',
                'type': str},
            ('--gnuplot-path',): {
                'help': 'The path to gnuplot\'s binary.',
                'type': str},
            ('--num-runs-per-instance',): {
                'help': 'The number of independent runs of the algorithm that '
                        'were performed on each instance. This is only used for '
                        'validating your dataset. ESA will automatically '
                        'determine the number from the file provided.',
                'type': int},
            ('--per-instance-statistic',): {
                'help': 'The statistic calculated over independent runs of the '
                        'algorithm on the same instance.',
                'type': str},
            ('--num-per-instance-bootstrap-samples', '--per-instance-n-bootstrap'): {
                'help': 'The number of (inner) bootstrap samples. That is, the '
                        'number of bootstrap samples used for independent runs '
                        'per instance. This is known to be a less important '
                        'parameter to set to a large value than the number of '
                        'outer bootstrap samples.',
                'type': _validate(int, 'The number of bootstrap samples per '
                                       'instance must be at least 5.',
                                  lambda x: int(x) > 5)},
            ('--log-level',): {
                'help': 'Controls the verbosity of the output. Choose from '
                        '"warning", "info" and "debug"',
                'type': str},
            ('--log-file',): {
                'help': 'The file to which ESA should log information.',
                'type': str},
            ('--num-observations',): {
                'help': 'The number of points for which ESA will calculate '
                        'statistics to determine whether or not the model '
                        'predictions are consistent with the observations.',
                'type': _validate(int, 'The number of observations must be a '
                                       'positive integer', 
                                  lambda x: int(x) > 0)},
            ('--observations',): {
                'help': 'Instead of providing the number of observations '
                        'you can also instead provide the locations of all of '
                        'the observations. Should be an array of instance sizes.',
                'type': str},
            ('--window', '--window-size'): {
                'help': 'The number of instances to be used in the sliding '
                        'bootstrap window.',
                'type': _validate(int, 'The number of instances in the window '
                                       'must be at least 10',
                                  lambda x: int(x) >= 10)},
            ('--runtime-cutoff',): {
                'help': 'The running time cutoff that you used with your ' 
                        'algorithm.',
                'type': _validate(float, 'The running time cutoff must be '
                                         'a positive number',
                                  lambda x: float(x) > 0)}
        }

        self.groups_in_order = ['Setup Arguments']
        self.argument_groups = {'Setup Arguments': self.setup_arguments,}
        self.group_help = {'Setup Arguments': 'These settings control the '
                                              'analysis performed by ESA'}
        # Location of the GPS source code directory
        esa_directory = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
        # File with hard-coded default values for all (optional) ESA parameters
        self.defaults = '{}/.esa_defaults.txt'.format(esa_directory)

    def parse_command_line_arguments(self):
        """parse_command_line_arguments
    
        Parses the command line arguments for ESA.
    
        Returns
        -------
        arguments: dict
            A dictionary containing the parsed arguments.
        """
        parser = argparse.ArgumentParser()
        for group_name in self.argument_groups:
            group = parser.add_argument_group(group_name)
            for arg in self.argument_groups[group_name]:
                group.add_argument(*_get_aliases(arg), dest=_get_name(arg), **self.argument_groups[group_name][arg])
        # Parse the command line arguments and convert to a dictionary
        args = vars(parser.parse_args())
        keys = list(args.keys())
        # Remove everything that is None so that we know to replace those values with scenario file arguments
        # instead.
        for arg in keys:
            if args[arg] is None:
                del args[arg]
        return args
   
    def parse_file_arguments(self, scenario_file, override_arguments={}):
        """parse_file_arguments
    
        Reads in the scenario file arguments, over-writes any of them with their
        override counterparts (for example, defined on the command line), if 
        applicable, and then saves them.
        """ 
        parsed_arguments = {}
        skipped_lines = []
        with open(scenario_file) as f_in:
            for line in f_in:
                # Remove any comments
                line = line.split('#')[0]
                # Strip whitespace
                line = line.strip()
                # Skip empty lines
                if len(line) == 0:
                    continue
                key = line.split(':')[0].strip()
                value = ':'.join(line.split(':')[1:]).strip()
                found = False
                # Check for a match in any of the argument types
                for group in self.argument_groups: 
                    for argument in self.argument_groups[group]:
                        if '--{}'.format(key) in _get_aliases(argument) or '-{}'.format(key) in argument:
                            # We found a match, store it under the argument's proper name, convert the
                            # value to it's proper type and raise an exception if it is invalid.
                            parsed_arguments[_get_name(argument)] \
                                = self.argument_groups[group][argument]['type'](value)
                            found = True
                            continue
                if found:
                    continue
                if not found:
                    skipped_lines.append(line)
        # Overwrite any argument definitions, as needed 
        for argument in override_arguments:
            parsed_arguments[argument] = override_arguments[argument]

        return parsed_arguments, skipped_lines        

    def parse_arguments(self, scenario_directory):
        """parse_arguments
        Parses the 
        arguments in the scenario file. Then adds default values for
        paramaters without definitions. Finally, validates all argument
        definitions, checks that needed files and directories exist, and then
        checks to make sure that all required arguements received definitions.
        
        Parameters
        ----------
        scenario_directory : str
            The path to the scenario directory

        Returns
        -------
        arguments : dict
            A dictionary mapping all GPS arguments to definitions.
        skipped_lines : list of str
            A list of all non-comment lines in the scenario file that were
            skipped.
        """
        skipped_lines = []
        # First parse the command line arguments
        # arguments = self.parse_command_line_arguments()
        # If a scenario file was provided, parse the arguments from it
        # If an experiment directory is specified, we will change to that directory
        with helper.cd(scenario_directory):
            try:
                arguments, skipped_lines = self.parse_file_arguments('configurations.txt', {})
            except IOError:
                raise IOError("The configuration.txt file could not be found from within "
                              "'{}' "
                              "".format(os.getcwd()))
        # Finally, load the default values of all ESA parameters 
        arguments, _ = self.parse_file_arguments(self.defaults, arguments)
        # Check that all parameters have defintions (optional parameters not specified by the
        # user will have already been included with default values)
        self._validate_all_arguments_defined(arguments)
        # Make sure all of the files and directories can be found
        _validate_files_and_directories(arguments, scenario_directory)

        return arguments, skipped_lines

    def _validate_all_arguments_defined(self, arguments):
        missing = []
        # iterate over all arguments
        for group in self.argument_groups: 
            for argument in self.argument_groups[group]:
                name = _get_name(argument)
                if name not in arguments:
                    missing.append(name)
        # The scenario file is the only argument that is *truely* optional
        #if 'scenario_file' in missing:
        #    missing.remove('scenario_file')
        if len(missing) > 0:
            raise TypeError('ESA was missing definitions for the following required arguments: {}'
                            ''.format(missing))       

               
                      
                    
def _get_name(names):
    name = names[0] if isinstance(names, tuple) else names
    name = name[2:]
    return name.replace('-','_')
 
def _validate(types, message=None, valid=lambda x: True):
    if not isinstance(types, tuple):
        types = (types, )
    def _check_valid(input_):
        valid_type = False
        for type_ in types:
            try:
                input_ = type_(input_)
                valid_type = True
            except:
                pass
        if not (valid_type and valid(input_)):
            if message is not None:
                raise argparse.ArgumentTypeError('{}. Provided "{}".'.format(message, input_))
            else:
                raise argparse.ArgumentTypeError('Input must be one of {}. Provided "{}".'.format(types, input_))
        return input_       
    return _check_valid
        
def _validate_files_and_directories(arguments, scenario_dir):
    with helper.cd(scenario_dir):
        files = ['file_name']
        for filename in files:            
            if not helper.isFile(arguments[filename]):
                raise IOError("The {} '{}' could not be found within the "
                              "directory '{}'."
                              "".format(filename.replace('_', ' '), 
                                        arguments[filename],
                                        os.getcwd()))
        directories = []
        for directory in directories:            
            if not helper.isDir(arguments[directory]):
                raise IOError("The {} '{}' could not be found within the "
                              "directory '{}'."
                              "".format(directory.replace('_', ' '), 
                                        arguments[directory], 
                                        os.getcwd()))

def _to_bool(string):
    if string == 'True':
       return True
    elif string == 'False':
        return False
    else:
        raise ValueError("Booleans must be 'True' or 'False'. Provided {}".format(string))
    
def _get_aliases(names):
    aliases = []
    for name in names:
        aliases.append(name)
        if name[:2] == '--':
            alias = '--{}'.format(name[2:].replace('-', '_'))
            if alias not in aliases:
                aliases.append(alias)
            alias = '--{}{}'.format(name[2:].split('-')[0],
                                    ''.join([token.capitalize() for token in name[2:].split('-')[1:]]))
            if alias not in aliases:
                aliases.append(alias)
    return tuple(aliases)

def _print_argument_documentation():
    """_print_argument_documentation

    Prints out documentation on each of the parameters formated
    to be included in the github readme file, including markdown.
    """
    def _table_row(header, content):
        return '<tr>{}{}</tr>'.format(_table_column(_bold(header)),
                                      _table_column(content))
    def _table_column(content):
        return '<td>{}</td>'.format(content)
    def _bold(header):
        return '<b>{}</b>'.format(header)
    def _list_of_code(aliases):
        return ', '.join([_code(alias.strip()[2:]) for alias in aliases])
    def _code(code):
        return '<code>{}</code>'.format(code)
    def _table(description, required, default, aliases):
        return  ('<table>\n{}\n{}\n{}\n</table>\n'
                 ''.format(_table_row('Description', _abreviations_to_italics(description)),
                           _table_row('Required' if required else 'Default',
                                      'Yes' if required else default),
                           _table_row('Aliases', _list_of_code(aliases))))
    def _abreviations_to_italics(content):
        abreviations = ['e.g.', 'i.e.', 'etc.', 'vs.']
        for token in abreviations:
            content = content.replace(token, '<i>{}</i>'.format(token))
        return content

    argument_parser = ArgumentParser()
    defaults, _ = argument_parser.parse_file_arguments(argument_parser.defaults, {})
    for group in argument_parser.groups_in_order:
        print('## {}\n'.format(group))
        print('{}\n'.format(_abreviations_to_italics(argument_parser.group_help[group])))
        arguments = sorted(list(argument_parser.argument_groups[group].keys()))
        for arg in arguments:
            name = _get_name(arg)
            print('### {}\n'.format(name))
            description = argument_parser.argument_groups[group][arg]['help']
            required = name not in defaults
            default = None if required else defaults[name]
            # Handle the one exception to the rule.
            if name == 'scenario_file':
                required = False
                default = None
            # Convert directories to code
            if '_dir' in name:
                default = _code(default)
            aliases = _get_aliases(arg)
            print(_table(description, required, default, aliases))
           
if __name__ == '__main__':
    _print_argument_documentation() 
