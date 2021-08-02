"""Contains all what you need to implement basic confic factory"""
import abc
import base64
import boto3
import botocore.exceptions
import functools
import json
import logging
import typing


# Exceptions
class ConfigException(Exception):
    """Base config exception"""
    def __init__(self, *args):
        super().__init__(*args)


class ConfigReaderException(ConfigException):
    """Base exception for config reader"""
    def __init__(self, *args):
        super().__init__(*args)


class ConfigLoaderException(ConfigException):
    """Base exception for config loader"""
    def __init__(self, *args):
        super().__init__(*args)


# Interfaces
class IConfigReader(abc.ABC):
    """Interface for config reader"""
    @abc.abstractmethod
    def read(self) -> str:
        """
        Reads the configuration

        :return: Configuration string
        :rtype: str
        """
        pass


class IConfigLoader(abc.ABC):
    """Interface for config loader"""
    @abc.abstractmethod
    def load(self, config_string: str) -> dict:
        """
        Load config config object from string

        :param config_string: Configuration string
        :type config_string: str
        :return: Configuration dictionary
        :rtype: dict
        """
        pass


class IConfig(abc.ABC):
    """Interface for config"""
    pass


# Readers
class SecretsManagerReader(IConfigReader):
    """Reads from secrets manager"""
    def __init__(self, secret_config: dict, secret_region: typing.Optional[str] = None):
        """
        :param secret_config: see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.get_secret_value
        :param secret_region: aws region
        """
        try:
            self.__client = boto3.client('secretsmananger') if secret_region is None else \
                boto3.client('secretsmanager', secret_region)
        except botocore.exceptions.ClientError as e:
            logging.getLogger().error(f"Error creating aws secrets manager client: {e!s}")
            raise ConfigReaderException(f"Exception getting aws secrets manager client")

        self.__secret_config = secret_config

    @functools.lru_cache(None)
    def read(self) -> str:
        """Reads config from secrets manager"""
        try:
            conf = self.__client(**self.__secret_config)

            if 'SecretString' in conf:
                return conf['SecretString']
            else:
                return str(base64.b64decode(conf['SecretBinary']))
        except botocore.exceptions.ClientError as e:
            logging.getLogger().error(f"Error reading secret {e.response['Error']['Code']}")
            raise ConfigReaderException(e.response['Error']['Code'])


# Loaders
class JSonLoader(IConfigLoader):
    """Load config from json format"""
    def load(self, config_string: str) -> dict:
        """Load config from JSon"""
        try:
            return json.loads(config_string)
        except json.JSONDecodeError as e:
            logging.getLogger().error(f"Error loading json config: {e.msg}")
            raise ConfigLoaderException(e.msg)


@functools.lru_cache(None)
def get_config(reader: IConfigReader, loader: IConfigLoader,
               config_class: typing.ClassVar[IConfig]):
    """
    Load config into a config class

    :param reader: Reader instance
    :param loader: Loader instance
    :param config_class: IConfig class
    :return: config_class instance
    """
    raw = reader.read()
    data = loader.load(raw)
    try:
        return config_class(**data)
    except TypeError as e:
        logging.getLogger().error(f"Error creating config: {e!s}")
        raise ConfigException(f"Error creating config: {e!s}")
