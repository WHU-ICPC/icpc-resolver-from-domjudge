from argparse import ArgumentParser

def argument_parser():
    parser = ArgumentParser()
    parser.add_argument('--config', help='config filename', default='config.json')
    return vars(parser.parse_args())
