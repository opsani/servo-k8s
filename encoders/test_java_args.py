import pytest
from java_args import describe, encode, \
    JavaArgsEncoderException, \
    EXC_NO_CURRENT_VALUE, EXC_UNPARSEABLE_VALUE, EXC_MULTI_ARGS, \
    EXC_RANGE_BOUNDARIES_MISMATCH, \
    EXC_RANGE_NO_LOWER_BOUND, EXC_RANGE_LOWER_BOUND_VIOLATION, \
    EXC_RANGE_NO_UPPER_BOUND, EXC_RANGE_UPPER_BOUND_VIOLATION, \
    EXC_RANGE_NO_STEP, EXC_RANGE_STEP_ZERO, EXC_RANGE_VALUE_STEP_REMAINDER

"""
Describe helper
"""


def test_describe_no_current_value_with_default():
    options = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3},
                            'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15}}}
    descriptor = describe(options, [])
    assert descriptor == {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3, 'value': 3},
                          'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15, 'value': 15}}


def test_describe_no_current_value_without_default():
    match = r"{}".format(EXC_NO_CURRENT_VALUE.format(setting='\\w+'))

    with pytest.raises(JavaArgsEncoderException, match=match):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}}, [])

    with pytest.raises(JavaArgsEncoderException, match=match):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}, [])


def test_describe_unsupported_settings_provided():
    options = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                            'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(options, ['java', '-server',
                                    '-XX:MaxHeapSize=5120m',
                                    '-XX:GCTimeRatio=50',
                                    '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'])
    assert descriptor == {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 5},
                          'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 50}}


def test_describe_wrong_value_format():
    match = r"{}".format(EXC_UNPARSEABLE_VALUE.format(value='[\\d\\w.]+', setting='\\w+', error='.+'))

    with pytest.raises(JavaArgsEncoderException, match=match):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5.2g'])

    with pytest.raises(JavaArgsEncoderException, match=match):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=None'])


def test_describe_multiple_duplicate_settings_provided():
    match = r"{}".format(EXC_MULTI_ARGS.format(prefixes='[\\w:-]+'))

    with pytest.raises(JavaArgsEncoderException, match=match):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5120m', '-XX:MaxHeapSize=6144m'])

    with pytest.raises(JavaArgsEncoderException, match=match):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=50', '-XX:GCTimeRatio=60'])


def test_describe_no_settings_provided():
    with pytest.raises(AssertionError, match='No settings for encoder java_args has been provided.'):
        describe({'settings': {}}, [])


def test_describe_no_config_provided():
    with pytest.raises(AssertionError, match='No configratuion for encoder java_args has been provided.'):
        describe(None, ['-XX:MaxHeapSize=1024m'])


def test_describe_wrong_config_type_provided():
    with pytest.raises(AssertionError,
                       match='Configuration argument for encoder java_args expected to be a dictionary.'):
        describe('settings', ['-XX:MaxHeapSize=1024m'])


"""
Encode helper
"""


def test_encode():
    encoded = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                   'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                     {'MaxHeapSize': 4,
                      'GCTimeRatio': 59})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_no_values_provided():
    with pytest.raises(AssertionError, match='No values to encode provided to java_args encoder.'):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                             'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}, {})


def test_encode_before_after_persist():
    encoded = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                      'before': ['java', '-server'],
                      'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                     {'MaxHeapSize': 4})
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m',
                       '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']


def test_encode_value_conversion():
    assert encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': .125}}},
                  {'MaxHeapSize': 1.625}) == ['-XX:MaxHeapSize=1664m']


def test_encode_range_type_setting_value_check():
    with pytest.raises(AssertionError, match=EXC_RANGE_NO_LOWER_BOUND.format(setting='MaxHeapSize')):
        encode({'settings': {'MaxHeapSize': {'max': 6, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(AssertionError, match=EXC_RANGE_NO_UPPER_BOUND.format(setting='MaxHeapSize')):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(AssertionError, match=EXC_RANGE_NO_STEP.format(setting='MaxHeapSize')):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6}}},
               {'MaxHeapSize': 2})

    with pytest.raises(AssertionError, match=EXC_RANGE_STEP_ZERO.format(setting='MaxHeapSize')):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 0}}},
               {'MaxHeapSize': 2})

    with pytest.raises(AssertionError, match=EXC_RANGE_VALUE_STEP_REMAINDER.format(setting='MaxHeapSize')):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 2.5})

    # with pytest.raises(AssertionError, match=EXC_RANGE_BOUNDARIES_MISMATCH.format(
    #         setting='MaxHeapSize', left=6, right=1)):
    with pytest.raises(AssertionError):
        encode({'settings': {'MaxHeapSize': {'min': 6, 'max': 1, 'step': 1}}},
               {'MaxHeapSize': 2})
