"""Example usage"""
import config_factory
import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class DemoConfig(config_factory.IConfig):
    """Demo configuration"""
    param1: str
    param2: int
    param3: typing.Optional[str] = None


def main():
    reader = config_factory.SecretsManagerReader({'SecretId': 'demo'})
    loader = config_factory.JSonLoader()
    cfg = config_factory.get_config(reader, loader, DemoConfig)
    print(cfg)


if __name__ == '__main__':
    main()
