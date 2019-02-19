import yaml


class JavaArgsEncoderException(Exception):
    pass


# Return list of zero or one arguments found in a list by specified prefix.
def get_arg_from_list(arg_prefixes, args):
    found_args = list(filter(lambda arg: any([arg.startswith(prefix) for prefix in arg_prefixes]), args))
    if len(found_args) > 1:
        raise JavaArgsEncoderException('[Decode multi] More than one argument for prefixes '
                                       '"{}" is not supported.'.format('", "'.format(arg_prefixes)))
    return found_args[0] if found_args else None


def check_range(name, value, options):
    assert value is not None, 'No value was provided for setting "{}" on encode ' \
                              'in java_args encoder.'.format(name)
    assert options['min'] is not None, 'Lower bound for setting "{}" was not provided.'.format(name)
    assert value >= options['min'], 'Value of setting "{}" is lower than defined lower bound ' \
                                    '({} < {}).'.format(name, value, options['min'])
    assert options['max'] is not None, 'Upper bound for setting "{}" was not provided.'.format(name)
    assert value <= options['max'], 'Value of setting "{}" is higher than defined upper bound ' \
                                    '({} < {}).'.format(name, value, options['max'])
    assert options['step'] is not None, 'Step for setting "{}" was not provided.'.format(name)
    assert value % options['step'] == 0, 'Value of setting "{}" cannot be divided by step ' \
                                         'without remainder.'.format(name)


class Encoder:

    def __init__(self, config):
        self.config = config

    def describe(self):
        settings = self.config.setdefault('settings', {})
        described = {}
        for name, opts in settings.items():
            described[name] = opts.copy()
        return described or None

    def encode_multi(self, values):
        before = self.config.get('before', [])
        after = self.config.get('after', [])
        settings = self.describe()
        medium = []
        for name, options in settings.items():
            value = values.get(name, None)
            if name == 'MaxHeapSize':
                check_range(name, value, options)
                medium.append('-XX:MaxHeapSize={}m'.format(int(value * 1024)))
            if name == 'GCTimeRatio':
                check_range(name, value, options)
                medium.append('-XX:GCTimeRatio={}'.format(value))
        return before + medium + after

    def decode_multi(self, data):
        decoded = {}
        settings = self.describe()
        for name, options in settings.items():
            if name == 'MaxHeapSize':
                arg = get_arg_from_list(['-XX:MaxHeapSize'], data)
                if arg:
                    try:
                        decoded[name] = int(arg.split('=')[1].rstrip('m')) / 1024
                    except ValueError as e:
                        raise ValueError(
                            'Could not parse value "{}" for setting "{}" on decode in encoder "{}".\n'
                            'Error: {}.'.format(arg.split('=')[1].rstrip('m'), name, 'java_args', str(e)))
            if name == 'GCTimeRatio':
                arg = get_arg_from_list(['-XX:GCTimeRatio'], data)
                if arg:
                    try:
                        decoded[name] = int(arg.split('=')[1])
                    except ValueError as e:
                        raise ValueError(
                            'Could not parse value "{}" for setting "{}" on decode in encoder "{}".\n'
                            'Error: {}.'.format(arg.split('=')[1].rstrip('m'), name, 'java_args', str(e)))
            # Handle default value
            if decoded.get(name, None) is None and \
                    options.get('default', None) is not None:
                decoded[name] = options['default']
        return decoded


def encode(options, values):
    return Encoder(options).encode_multi(values)


def describe(options, current_data):
    encoder = Encoder(options)
    desc = encoder.describe()
    values = encoder.decode_multi(current_data)

    for name, setting in desc.items():
        try:
            setting['value'] = values[name]
        except KeyError as e:
            raise KeyError('Could not find current value for setting "{}" on describe in encoder "{}". '
                           'No default value has been provided.'.format(str(e).strip("'"), 'java_args'))

    return desc


if __name__ == '__main__':
    options = yaml.load(open('../config.yaml'))['k8s']['deployments']['d1']['command']['encoder']
    input_data = ['java', '-server',
                  '-XX:MaxHeapSize=2304m', '-XX:GCTimeRatio=92',
                  '-javaagent:/tmp/newrelic/newrelic.jar', '-Dnewrelic.environment=l1', '-jar', '/app.jar']
    data_to_encode = {'MaxHeapSize': 2.75, 'GCTimeRatio': 10}
    # res = describe(options, input_data)
    # print(res)
    res = encode(options, data_to_encode)
    print(res)
