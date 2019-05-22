"""Configuration file to define devices and midi controls."""
INPUT_DEVICES = ['Faderfox UC4', 'XONE:K2', ]
OUTPUT_DEVICES = ['Circuit', ]

CONTROLS = {
    16: {
        'in_channel': 15,
        'translate': 12,
        'out_channel': 16,
        'description': 'Synth1 Volume',
    },
    17: {
        'in_channel': 15,
        'translate': 14,
        'out_channel': 16,
        'description': 'Synth2 Volume',
    },
    18: {
        'in_channel': 15,
        'translate': '1>8',
        'out_channel': 16,
        'description': 'Synth2 Volume',
    },
    19: {
        'in_channel': 15,
        'translate': '1>9',
        'out_channel': 16,
        'description': 'Synth2 Volume',
    },
    56: {
        'in_channel': 4,
        'translate': 12,
        'out_channel': 16,
        'description': 'Synth1 Volume',
    },
    57: {
        'in_channel': 4,
        'translate': 14,
        'out_channel': 16,
        'description': 'Synth2 Volume',
    },
}
