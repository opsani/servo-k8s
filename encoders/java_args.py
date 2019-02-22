import yaml


# JavaOptsEncoderException = type('JavaOptsEncoderException', (BaseException,), {})
# NoValueToEncodeException = type('NoValueToEncodeException', (JavaOptsEncoderException,), {})
# NoValueToDecodeException = type('NoValueToDecodeException', (JavaOptsEncoderException,), {})
# InvalidValueException = type('InvalidValueException', (JavaOptsEncoderException,), {})
# NoLowerBoundException = type('NoLowerBoundException', (JavaOptsEncoderException,), {})
# NoUpperBoundException = type('NoUpperBoundException', (JavaOptsEncoderException,), {})
# UpperBoundViolationException = type('UpperBoundViolationException', (JavaOptsEncoderException,), {})
# LowerBoundViolationException = type('LowerBoundViolationException', (JavaOptsEncoderException,), {})
# BoundariesCollisionException = type('BoundariesCollisionException', (JavaOptsEncoderException,), {})
# NoStepException = type('NoStepException', (JavaOptsEncoderException,), {})
# NoTypeException = type('NoTypeException', (JavaOptsEncoderException,), {})
# StepIsNotZeroException = type('StepIsNotZeroException', (JavaOptsEncoderException,), {})
# ValueStepRemainderException = type('ValueStepRemainderException', (JavaOptsEncoderException,), {})
# DuplicateSettingsException = type('DuplicateSettingsException', (JavaOptsEncoderException,), {})


class MaxHeapSizeSetting:
    name = 'MaxHeapSize'
    type = 'range'
    unit = 'gigabytes'
    can_relax = True

    def __init__(self, config):
        self.check_config(config)
        self.min = config.get('min')
        self.max = config.get('max')
        self.step = config.get('step')
        self.default = config.get('default')

    def check_config(self, config):
        if not config:
            raise Exception('No configuration provided for setting encoder {} in java-opts encoder.'.format(self.name))
        minv = config.get('min')
        maxv = config.get('max')
        step = config.get('step')
        if minv is None:
            raise Exception('No min value provided for setting {} in java-opts encoder.'.format(self.name))
        if maxv is None:
            raise Exception('No max value provided for setting {} in java-opts encoder.'.format(self.name))
        if step is None:
            raise Exception('No step value provided for setting {} in java-opts encoder.'.format(self.name))
        if not isinstance(minv, (int, float)):
            raise Exception('Min value is neither int nor float in setting {} of java-opts encoder. '
                            'It\'s value is "{}".'.format(self.name, minv))
        if not isinstance(maxv, (int, float)):
            raise Exception('Max value is neither int nor float in setting {} of java-opts encoder. '
                            'It\'s value is "{}".'.format(self.name, maxv))
        if not isinstance(step, (int, float)):
            raise Exception('Step value is neither int nor float in setting {} of java-opts encoder. '
                            'It\'s value is "{}".'.format(self.name, step))
        if minv > maxv:
            raise Exception('Lower boundary is higher than upper boundary in setting {} '
                            'of java-opts encoder.'.format(self.name))
        if minv == maxv and step > 0:
            raise Exception('Step for setting must be 0 when min value == max value.')
        # Relaxation of boundaries
        if not self.can_relax:
            default_min = getattr(self, 'min', None)
            default_max = getattr(self, 'max', None)
            if default_min is None:
                raise Exception('Default min value for setting {} must be provided to disallow its relaxation.')
            elif minv < default_min:
                raise Exception('Min value for setting {} cannot be lower than {}. It is {} now.'.format(
                    self.name, default_min, minv))
            if default_max is None:
                raise Exception('Default max value for setting {} must be provided to disallow its relaxation.')
            elif maxv < default_max:
                raise Exception('Max value for setting {} cannot be lower than {}. It is {} now.'.format(
                    self.name, default_max, maxv))

    def describe(self, data):
        return (self.name, {
            'type': self.type,
            'min': self.min,
            'max': self.max,
            'step': self.step,
            'value': self.decode_multi(data),
            'unit': self.unit,
        })

    def validate_values(self, values):
        value = values.get(self.name)
        if value is None:
            raise Exception('No value provided to encode for setting {}'.format(self.name))
        if not isinstance(value, (float, int)):
            raise Exception('Value in setting {} must be either integer or float, '
                            'but we got "{}".'.format(value, self.name))
        if value < self.min:
            raise Exception('Value "{}" is violating lower bound in setting {}'.format(value, self.name))
        if value > self.max:
            raise Exception('Value "{}" is violating upper bound in setting {}'.format(value, self.name))
        if self.min < self.max and (value - self.min) % self.step != 0:
            raise Exception('Value "{}" is violating step requirement in setting {}'.format(value, self.name))
        return value

    def encode_multi(self, values):
        value = self.validate_values(values)
        return ['-XX:{}={}m'.format(self.name, int(round(value * 1024)))]

    def validate_data(self, data):
        found_args = list(filter(lambda arg: arg.startswith('-XX:{}'.format(self.name)), data))
        if len(found_args) > 1:
            raise Exception('Received duplicate values for setting {} on decode'.format(self.name))
        if not found_args and self.default is None:
            raise Exception('No value found to decode for setting {} and neither '
                            'default value was provided.'.format(self.name))
        return found_args

    def decode_multi(self, data):
        args = self.validate_data(data)
        if args:
            arg = args[0]
            try:
                return int(arg.split('=')[1].rstrip('m')) / 1024
            except ValueError as e:
                raise Exception('Invalid value to decode for setting {}. '
                                'Error: {}. Arg: {}'.format(self.name, str(e), arg))
        return self.default


class GCTimeRatioSetting:
    pass


supported_settings = {
    'MaxHeapSize': MaxHeapSizeSetting,
    # 'GCTimeRatio': GCTimeRatioSetting,
}


class NewEncoder:
    def __init__(self, config):
        if config is None:
            config = {}
        assert isinstance(config, dict), 'Configuration object for java-opts encoder is expected to be ' \
                                         'of a dictionary type'
        self.config = config
        self.settings = {}

        requested_settings = self.config.get('settings') or {}
        for name, setting in requested_settings.items():
            try:
                setting_class = supported_settings[name]
            except KeyError:
                raise Exception('Setting "{}" is not supported in jvm-opts encoder.'.format(name))
            self.settings[name] = setting_class(setting or {})

    def describe(self, data):
        for setting in self.settings.values():
            yield setting.describe(data)

    def encode_multi(self, values):
        values_to_encode = values.copy()

        yield from self.config.get('before', [])

        for name, setting in self.settings.items():
            yield from setting.encode_multi({name: values_to_encode.pop(name, None)})

        yield from self.config.get('after', [])

        if values_to_encode:
            raise Exception('We received settings to encode we do not support {}'.format(list(values_to_encode.keys())))


def encode(config, values):
    return list(NewEncoder(config).encode_multi(values))


def describe(config, data):
    return dict(NewEncoder(config).describe(data))


if __name__ == '__main__':
    encoder_section = yaml.load(open('../config.yaml'))['k8s']['deployments']['d1']['command']['encoder']

    # Describe
    current_data = ['java', '-server',
                    '-XX:MaxHeapSize=1024m',
                    '-XX:GCTimeRatio=92',
                    '-javaagent:/tmp/newrelic/newrelic.jar', '-Dnewrelic.environment=l1', '-jar', '/app.jar']
    desc = describe(encoder_section, current_data)
    print('Described', desc)

    # Encode
    data_to_encode = {'MaxHeapSize': 13}  # , 'GCTimeRatio': 10}
    encoded = encode(encoder_section, data_to_encode)
    print('Encoded', encoded)
