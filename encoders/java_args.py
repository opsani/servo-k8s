import yaml


class JavaArgsEncoderException(Exception):
    pass


EXC_RANGE_NO_VALUE = 'No value was provided for setting "{setting}" on encode in java_args encoder.'
EXC_RANGE_NO_LOWER_BOUND = 'Lower bound for setting "{setting}" was not provided on encode in java_args encoder.'
EXC_RANGE_LOWER_BOUND_VIOLATION = 'Value of setting "{setting}" is lower than defined lower bound ({left} < {right})' \
                                  ' on encode in java_args encoder.'
EXC_RANGE_NO_UPPER_BOUND = 'Upper bound for setting "{setting}" was not provided on encode in java_args encoder.'
EXC_RANGE_UPPER_BOUND_VIOLATION = 'Value of setting "{setting}" is higher than defined upper bound ({left} < {right})' \
                                  ' on encode in java_args encoder.'
EXC_RANGE_BOUNDARIES_MISMATCH = 'Upper bound for setting "{setting}" is lower than the lower bound ' \
                                '({left} < {right}) on encode in java_args encoder.'
EXC_RANGE_NO_STEP = 'Step for setting "{setting}" was not provided on encode in java_args encoder.'
EXC_RANGE_STEP_ZERO = 'Step for setting "{setting}" cannot be set to 0 on encode in java_args encoder.'
EXC_RANGE_VALUE_STEP_REMAINDER = 'Value of setting "{setting}" cannot be divided by step without remainder' \
                                 ' on encode in java_args encoder.'

EXC_MULTI_ARGS = 'More than one argument for prefix "{prefixes}" is not supported on decode in java_args encoder.'

EXC_UNPARSEABLE_VALUE = 'Could not parse value "{value}" for setting "{setting}" on decode in encoder java_args.\n' \
                        'Error: {error}.'

EXC_NO_CURRENT_VALUE = 'Could not find current value for setting "{setting}" on describe in encoder java_args. ' \
                       'No default value has been provided.'


# Return list of zero or one arguments found in a list by specified prefix.
def get_arg_from_list(arg_prefixes, args):
    found_args = list(filter(lambda arg: any([arg.startswith(prefix) for prefix in arg_prefixes]), args))
    if len(found_args) > 1:
        raise JavaArgsEncoderException(EXC_MULTI_ARGS.format(prefixes='", "'.join(arg_prefixes)))
    return found_args[0] if found_args else None


def check_range(name, value, options):
    assert value is not None, EXC_RANGE_NO_VALUE.format(setting=name)
    minv = options.get('min', None)
    maxv = options.get('max', None)
    assert minv is not None, EXC_RANGE_NO_LOWER_BOUND.format(setting=name)
    assert maxv is not None, EXC_RANGE_NO_UPPER_BOUND.format(setting=name)
    assert minv <= maxv, EXC_RANGE_BOUNDARIES_MISMATCH.format(setting=name, left=minv, right=maxv)
    assert value >= minv, EXC_RANGE_LOWER_BOUND_VIOLATION.format(setting=name, left=value, right=minv)
    assert value <= maxv, EXC_RANGE_UPPER_BOUND_VIOLATION.format(setting=name, left=value, right=maxv)
    step = options.get('step', None)
    assert step is not None, EXC_RANGE_NO_STEP.format(setting=name)
    assert step > 0, EXC_RANGE_STEP_ZERO.format(setting=name)
    assert value % step == 0, EXC_RANGE_VALUE_STEP_REMAINDER.format(setting=name)


class Encoder:

    def __init__(self, config):
        assert config, 'No configratuion for encoder java_args has been provided.'
        assert isinstance(config, dict), 'Configuration argument for encoder java_args expected to be a dictionary.'
        assert 'settings' in config and config['settings'], 'No settings for encoder java_args has been provided.'
        self.config = config

    def describe(self):
        settings = self.config.setdefault('settings', {})
        described = {}
        for name, opts in settings.items():
            described[name] = opts.copy()
        return described or None

    def encode_multi(self, values):
        assert values, 'No values to encode provided to java_args encoder.'
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
                        raise JavaArgsEncoderException(EXC_UNPARSEABLE_VALUE.format(value=arg.split('=')[1].rstrip('m'),
                                                                                    setting=name, error=str(e)))
            if name == 'GCTimeRatio':
                arg = get_arg_from_list(['-XX:GCTimeRatio'], data)
                if arg:
                    try:
                        decoded[name] = int(arg.split('=')[1])
                    except ValueError as e:
                        raise JavaArgsEncoderException(EXC_UNPARSEABLE_VALUE.format(value=arg.split('=')[1].rstrip('m'),
                                                                                    setting=name, error=str(e)))
            # Handle default value
            current_value = decoded.get(name, None)
            default_value = options.get('default', None)
            if default_value is not None and current_value is None:
                decoded[name] = options['default']
        return decoded


def encode(encoder_options, values):
    encoder = Encoder(encoder_options)
    encoded = encoder.encode_multi(values)
    assert encoded, 'No settings to encode on encode in java_args encoder. Got "{}" as input values.'.format(values)
    return encoded


def describe(encoder_options, current_data):
    encoder = Encoder(encoder_options)
    desc = encoder.describe()
    values = encoder.decode_multi(current_data)

    for name, setting in desc.items():
        try:
            setting['value'] = values[name]
        except KeyError as e:
            raise JavaArgsEncoderException(EXC_NO_CURRENT_VALUE.format(setting=str(e).strip("'")))

    return desc


if __name__ == '__main__':
    encoder_section = yaml.load(open('../config.yaml'))['k8s']['deployments']['d1']['command']['encoder']
    input_data = ['java', '-server',
                  '-XX:MaxHeapSize=2304m', '-XX:GCTimeRatio=92',
                  '-javaagent:/tmp/newrelic/newrelic.jar', '-Dnewrelic.environment=l1', '-jar', '/app.jar']
    data_to_encode = {'MaxHeapSize': 2.75, 'GCTimeRatio': 10}
    # res = describe(options, input_data)
    # print(res)
    res = encode(encoder_section, data_to_encode)
    print(res)
