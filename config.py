"""Configuration file to define devices and midi controls."""
INPUT_DEVICES = ['Faderfox UC4', 'XONE:K2', ]
OUTPUT_DEVICES = ['Circuit', ]

CONTROLS = {
    16: {
        'in_channel': 14,
        'control': 12,
        'out_channel': 15,
        'description': 'Synth1 Volume',
    },
    17: {
        'in_channel': 14,
        'control': 14,
        'out_channel': 15,
        'description': 'Synth2 Volume',
    },
    56: {
        'in_channel': 1,
        'control': 12,
        'out_channel': 15,
        'description': 'Synth1 Volume',
    },
    57: {
        'in_channel': 1,
        'control': 14,
        'out_channel': 15,
        'description': 'Synth2 Volume',
    },
}
